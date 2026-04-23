#!/usr/bin/env python3
"""
PDF 파일명을 연구자 스타일로 정규화: {FirstAuthor}_{Year}_{short_title}.pdf

파일명 패턴 파싱 우선순위:
1. "Author et al. - YYYY - Title" / "Author and Author - YYYY - Title"
2. "Journal - YYYY - Author - Title"
3. PDF 메타데이터 (title, author)
4. 원 파일명을 기반으로 한 heuristic + 알려진 논문 매핑

사용: python3 normalize_filename.py <input.pdf> → 정규화된 basename 출력
"""
import sys
import re
import unicodedata
from pathlib import Path


# 제목 키워드에서 제거할 stop words
STOP_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or", "but",
    "is", "are", "was", "were", "be", "been", "being",
    "with", "by", "from", "that", "this", "these", "those",
    "how", "why", "what", "when", "where", "which", "who",
    "as", "it", "its", "their", "his", "her",
    "does", "do", "did", "can", "could", "would", "should",
    "into", "about", "across", "through", "between", "among",
    "an", "than", "then", "also", "not", "no",
}


def strip_diacritics(s: str) -> str:
    """Löffler → Loffler"""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_token(tok: str, lower: bool = True) -> str:
    tok = strip_diacritics(tok)
    tok = re.sub(r"[^A-Za-z0-9]+", "", tok)
    return tok.lower() if lower else tok


def title_keywords(title: str, max_words: int = 6) -> list[str]:
    """제목에서 의미있는 단어 추출."""
    title = strip_diacritics(title)
    # punctuation → space
    t = re.sub(r"[^A-Za-z0-9\s]+", " ", title)
    words = [w for w in t.split() if w]
    keep = []
    for w in words:
        lw = w.lower()
        if lw in STOP_WORDS:
            continue
        if len(lw) < 2:
            continue
        keep.append(lw)
        if len(keep) >= max_words:
            break
    return keep


def parse_author_first(authors_str: str) -> str:
    """'Löffler et al.' → 'Loffler'; 'Buss and Spencer' → 'BussSpencer'; 'Smith' → 'Smith'."""
    s = authors_str.strip()
    # "et al." 제거
    s = re.sub(r"\bet\s+al\.?", "", s, flags=re.IGNORECASE).strip()
    # " and " / " & " 로 분리
    parts = re.split(r"\s+(?:and|&)\s+", s, flags=re.IGNORECASE)
    if len(parts) == 1:
        return clean_token(parts[0], lower=False).capitalize()
    if len(parts) == 2:
        # Buss and Spencer → BussSpencer
        a = clean_token(parts[0], lower=False)
        b = clean_token(parts[1], lower=False)
        return (a.capitalize() + b.capitalize()) if a and b else (a or b).capitalize()
    # 3명 이상 → 첫 번째만
    return clean_token(parts[0], lower=False).capitalize()


def parse_from_filename(fname: str) -> dict | None:
    """파일명에서 저자·연도·제목 추출. 실패 시 None."""
    stem = Path(fname).stem
    # 선행 번호(5 Title) 제거
    stem = re.sub(r"^\d+\s+", "", stem)

    # Pattern A: "Author et al. - YYYY - Title"
    # Pattern B: "Author1 and Author2 - YYYY - Title"
    # Pattern C: "Author - YYYY - Title"
    m = re.match(r"^([A-ZÄÖÜŁ][A-Za-zÄÖÜäöüłöß\'\-]+(?:\s+(?:and|&)\s+[A-ZÄÖÜŁ][A-Za-zÄÖÜäöüłöß\'\-]+)?(?:\s+et\s+al\.?)?)\s*-\s*(\d{4})\s*-\s*(.+)$", stem)
    if m:
        return {"author": parse_author_first(m.group(1)), "year": m.group(2), "title": m.group(3).strip()}

    # Pattern D: "Journal Name - YYYY - AuthorLast - Title"
    # e.g. "Child Dev Perspectives - 2011 - Zhou - Commonalities and Differences..."
    m = re.match(r"^[A-Za-z][A-Za-z\s&\.\-]{4,60}\s+-\s+(\d{4})\s+-\s+([A-ZÄÖÜŁ][A-Za-zÄÖÜäöüłöß\'\-]+)\s+-\s+(.+)$", stem)
    if m:
        return {"author": parse_author_first(m.group(2)), "year": m.group(1), "title": m.group(3).strip()}

    return None


def extract_pdf_metadata(pdf_path: Path) -> dict:
    """PyPDF2 메타로 보강."""
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            pdf = PyPDF2.PdfReader(f)
            info = pdf.metadata or {}
            return {
                "title": (info.get("/Title") or "").strip(),
                "author": (info.get("/Author") or "").strip(),
                "pages": len(pdf.pages),
            }
    except Exception:
        return {"title": "", "author": "", "pages": 0}


# 알려진 논문(파일명 → 정규명) 매핑. 필요 시 확장.
# key: normalized stem (lowercase, alphanumeric only, first 50 chars)
KNOWN_MAPPING: dict[str, tuple[str, str, list[str]]] = {
    # (Author, Year, [title keywords])
    "theunityanddiversityofexecutivefunctionsandthei": ("Miyake", "2000", ["unity", "diversity", "EF"]),
    "thenatureandorganizationofindividualdifference": ("Miyake", "2012", ["nature", "organization", "individual", "differences", "EF"]),
    "unityanddiversityofexecutivefunctionsindividua": ("Friedman", "2017", ["unity", "diversity", "EF", "individual"]),
    "atruereflectionofexecutivefunctioningorarepres": ("Sambol", "2023", ["task", "specific", "variance", "unity", "diversity"]),
    "thefactorstructureofexecutivefunctionsmeasured": ("Loffler", "2025", ["ERP", "factor", "structure", "EF"]),
    "fractionationofexecutivefunctionsinadolescents": ("Segura", "2022", ["Iran", "fractionation", "EF"]),
    "crosscountrybrazilandiraninvarianceoffraction": ("Segura", "2023", ["Brazil", "Iran", "invariance"]),
    "psychometricpropertiesofthefiveexecutivefuncti": ("Wulanyani", "2024", ["Indonesia", "five", "EF", "tests"]),
    "theunitydiversityframeworkofexecutivefunctions": ("Guo", "2025", ["older", "adults", "behavioral", "neural"]),
    "thepsychometricstructureofexecutivefunctionsas": ("Rosales", "2023", ["psychometric", "network", "modeling"]),
    "factoranalyticevidenceforthecomplexityofthedel": ("McFarland", "2020", ["DKEFS", "factor", "complexity"]),
    "alatentvariableapproachtoexecutivecontrolinhea": ("AdroverRoig", "2012", ["latent", "variable", "healthy", "ageing"]),
    "neurocognitivearchitectureofexecutivefunctions": ("Ambrosini", "2019", ["neurocognitive", "architecture", "EF"]),
    "theroleofbilingualinteractionalcontextsinpred": ("Hartanto", "2020", ["bilingual", "interactional", "context"]),
    "thestructureofexecutivefunctionsinathletesalate": ("Brimmell", "2025", ["athletes", "latent", "variable"]),
    "genomicsemmodellingofdiverseexecutivefunctiong": ("Perry", "2024", ["GenomicSEM", "GWAS", "EF"]),
    "exploringthecontributionofexecutivefunctionsto": ("Adrian", "2019", ["driving", "EF", "aging"]),
    "theunityanddiversityofexecutivefunctionsanetwo": ("Karr", "2022", ["network", "approach", "life", "span"]),
    "unityordiversityinexecutivefunctionsexaminingt": ("Veraksa", "2025", ["three", "factor", "young", "children"]),

    # HUNT-010
    "thecommonfactorofexecutivefunctionsmeasuresno": ("Loffler", "2024", ["common", "factor", "speed", "uptake"]),
    "theroleofprefrontalcortexincognitivecontrolan": ("Friedman", "2021", ["PFC", "cognitive", "control", "EF"]),
    "adversityisassociatedwithlowergeneralprocessi": ("Vermeent", "2025", ["adversity", "processing", "speed", "EF"]),
    "processingspeedworkingmemoryandexecutivefuncti": ("Frischkorn", "2019", ["processing", "speed", "WM", "intelligence"]),
    "integratingtheswitchinginhibitionandupdatingm": ("Jewsbury", "2016", ["CHC", "switching", "inhibition", "updating"]),
    "dimensionalityofexecutivefunctionsandprocessin": ("Vanhala", "2023", ["dimensionality", "EF", "speed", "preschoolers"]),
    "genomewideassociationstudyshowsthatexecutivef": ("Hatoum", "2022", ["GWAS", "GABAergic", "cEF"]),

    # HUNT-034
    "neweverythingnewiswellforgottenoldvygotskyl": ("Bodrova", "2011", ["Vygotsky", "Luria", "EF"]),
    "verbalregulationofmotorbehaviorsovietresearch": ("Wozniak", "1972", ["verbal", "regulation", "motor", "Soviet"]),
    "arluriaandthehistoryofrussianneuropsychology": ("Glozman", "2007", ["Luria", "Russian", "neuropsychology"]),
    "contemporaryneuropsychologyandthelegacyofluria": ("Goldberg", "2019", ["Luria", "legacy", "neuropsychology"]),
    "scopeandperspectivesofneuroimagingandneurostim": ("Panikratova", "2022", ["neuroimaging", "Luria", "Vygotsky"]),

    # HUNT-035
    "makebelieveplaywellspringfordevelopmentofself": ("Berk", "2006", ["make", "believe", "self", "regulation"]),
    "playandselfregulationlessonsfromvygotsky": ("Bodrova", "2013", ["play", "self", "regulation", "Vygotsky"]),
    "theroleofmakebelieveplayinthedevelopmentofexe": ("Berk", "2013", ["make", "believe", "EF", "children"]),
    "vygotskianandpostvygotskianviewsonchildrenspla": ("Bodrova", "2015", ["Vygotskian", "children", "play"]),
    "vygotskystheoryinplayearlychildhoodeducation": ("Smolucha", "2021", ["Vygotsky", "theory", "play", "ECE"]),
    "engagementinsocialpretendplaypredictspreschool": ("White", "2021", ["pretend", "play", "EF", "gains"]),
    "dochildrenneedadultsupportduringsociodramaticp": ("Veresov", "2021", ["adult", "support", "sociodramatic", "EF"]),
    "thevalueofpretendplayforsocialcompetenceinear": ("SmitsvanderNat", "2024", ["pretend", "play", "social", "competence"]),
    "examiningtherelationbetweenadultscaffoldingof": ("Duval", "2023", ["adult", "scaffolding", "make", "believe"]),
    "playworldsandexecutivefunctionsinchildrentheori": ("Fleer", "2019", ["playworlds", "EF", "cultural", "historical"]),
    "thezoneofproximaldevelopmentinplayandlearning": ("Hakkarainen", "2008", ["ZPD", "play", "learning"]),

    # HUNT-020
    "rethinkingexecutivefunctionanditsdevelopment": ("Doebel", "2020", ["rethinking", "EF", "development"]),
    "reconcilingthecontextdependencyanddomaingene": ("Zelazo", "2022", ["reconciling", "context", "domain", "general"]),
    "adynamicalreconceptualizationofexecutivefuncti": ("Perone", "2020", ["dynamical", "reconceptualization", "EF"]),
    "universalityandcontextspecificityinearlyexecu": ("Miller", "2023", ["universality", "context", "specificity"]),
    "executivefunctionsinsocialcontextimplications": ("Munakata", "2021", ["EF", "social", "context"]),
    "executivefunctiondebunkinganoverprizedconstru": ("Demetriou", "2024", ["EF", "debunking", "overprized"]),
    "thedevelopmentofexecutivefunctionmechanismsof": ("Ibbotson", "2023", ["mechanisms", "functional", "pressures"]),
    "anewerafortheexecutivefunctionresearchonthet": ("Zink", "2020", ["distributed", "EF", "centralized"]),
    "whydoesntexecutivefunctiontrainingimproveaca": ("Niebaum", "2022", ["EF", "training", "contextual"]),
    "consideringrolesoftheexecutivefunctionsinthes": ("Cartwright", "2024", ["reading", "EF", "meta", "analysis"]),

    # HUNT-012
    "developmentofhotandcoolexecutivefunctionduring": ("Prencipe", "2011", ["hot", "cool", "EF", "adolescence"]),
    "hotandcoolexecutivefunctioninchildhoodandadol": ("Zelazo", "2012", ["hot", "cool", "EF", "childhood"]),
    "executivefunctionandpsychopathologyaneurodevelo": ("Zelazo", "2020", ["EF", "psychopathology", "neurodevelopmental"]),
    "assessmentofhotandcoolexecutivefunctioninyoung": ("Hongwanishkul", "2005", ["hot", "cool", "EF", "young", "children"]),
    "relationshipbetweencoolandhotexecutivefunctio": ("Moriguchi", "2021", ["cool", "hot", "EF", "fNIRS"]),
    "evaluatingthedistinctionbetweencoolandhotexec": ("Moriguchi", "2023", ["evaluating", "distinction", "cool", "hot"]),
    "hotandcoolexecutivefunctionsinadolescenceadeve": ("Poon", "2018", ["hot", "cool", "adolescence"]),
    "associationsbetweenanddevelopmentofcoolandho": ("OToole", "2018", ["cool", "hot", "EF", "early", "childhood"]),
    "componentsofsocioeconomicstatusdifferentiallyp": ("Demko", "2025", ["SES", "cool", "hot", "EF"]),
    "predictorsofexecutivefunctionamong2yearoldsfr": ("Nimmapirat", "2023", ["Thai", "2", "year", "olds", "EF"]),

    # HUNT-016
    "commonalitiesanddifferencesintheresearchonchil": ("Zhou", "2012", ["EC", "EF", "integration", "self", "regulation"]),
    "executiveattentionandeffortfulcontrollinkingt": ("Rothbart", "2007", ["executive", "attention", "EC", "genes"]),
    "commonmechanismsofexecutiveattentionunderlieex": ("Tiego", "2020", ["common", "attention", "EF", "EC"]),
    "selfregulationinpreschoolchildrenfactorstructu": ("Kalin", "2021", ["preschool", "EC", "EF", "factor"]),
    "selfregulationinpreschoolareexecutivefunction": ("Heinze", "2024", ["preschool", "EF", "EC", "overlapping"]),
    "measurementofselfregulationinearlychildhoodrel": ("Lin", "2019", ["measurement", "EC", "EF"]),
    "selfregulationinelementaryschooldoteacherrepo": ("Weiss", "2023", ["elementary", "EC", "EF", "codevelop"]),
    "howdoesthebroaderconstructofselfregulationrel": ("Gagne", "2021", ["self", "regulation", "emotion", "regulation"]),
    "thedevelopmentalmechanismsofselfregulationinyo": ("Zhang", "2019", ["developmental", "mechanisms", "self", "regulation"]),
    "theinteractionbetweennegativeemotionalityandef": ("Moran", "2013", ["negative", "emotionality", "EC"]),

    # HUNT-015
    "selfdeterminationtheoryandthefacilitationofin": ("Ryan", "2000", ["SDT", "intrinsic", "motivation"]),
    "selfdeterminationtheoryamacrotheoryofhumanmot": ("Deci", "2008", ["SDT", "macrotheory", "motivation"]),
    "intrinsicandextrinsicmotivationfromaselfdeter": ("Ryan", "2020", ["intrinsic", "extrinsic", "SDT", "education"]),
    "studentmotivationandassociatedoutcomesametaan": ("Howard", "2021", ["student", "motivation", "SDT", "meta"]),
    "selfdeterminationtheoryappliedtophysicaleducat": ("Vasconcellos", "2020", ["SDT", "physical", "education", "meta"]),
    "testingacontinuumstructureofselfdeterminedmot": ("Howard", "2017", ["continuum", "SDT", "meta", "analysis"]),
    "applyingselfdeterminationtheorytoeducationreg": ("Guay", "2021", ["SDT", "education", "regulation"]),
    "applyingselfdeterminationtheorytoeducationalpr": ("Niemiec", "2009", ["SDT", "autonomy", "competence", "classroom"]),
    "pathwaystostudentmotivationametaanalysisofant": ("Bureau", "2021", ["pathways", "motivation", "autonomous"]),
    "twelvetipstostimulateintrinsicmotivationinstud": ("Kusurkar", "2011", ["tips", "intrinsic", "autonomy", "SDT"]),

    # HUNT-017
    "dynamicfieldtheoryofexecutivefunctionidentify": ("McCraw", "2024", ["DFT", "EF", "neurocognitive", "markers"]),
    "theemergentexecutiveadynamicfieldtheoryofthe": ("BussSpencer", "2014", ["emergent", "DFT", "EF"]),
    "integratingattentionworkingmemoryandwordlear": ("Spencer", "2025", ["WOLVES", "DFT", "EF", "integrating"]),
    "thedimensionalchangecardsortdccsamethodofass": ("Zelazo", "2006", ["DCCS", "protocol", "EF"]),
    "ameetanalysisofthedimensionalchangecardsort": ("Doebel", "2015", ["DCCS", "meta", "analysis"]),
    "disentanglingdimensionsinthedimensionalchange": ("Kloo", "2005", ["dimensions", "DCCS"]),
    "childdevelopment2013ramscardualroutestocognit": ("Ramscar", "2013", ["dual", "routes", "cognitive", "flexibility"]),

    # HUNT-036
    "crossculturaldevelopmentalpsychologyintegrati": ("Amir", "2020", ["cross", "cultural", "developmental", "WEIRD"]),
    "allpsychologiesareindigenousaddressinghistori": ("Dvorakova", "2025", ["indigenous", "WEIRD", "colonialism"]),
    "advancingequityincrossculturalpsychologyemb": ("Anjum", "2024", ["equity", "cross", "cultural", "epistemologies"]),
    "considerationofcultureincognitionhowwecanenri": ("Gutchess", "2022", ["culture", "cognition", "methodology"]),
    "indigenouscommunitypsychologiesdecolonizationa": ("Ciofalo", "2022", ["indigenous", "community", "decolonization"]),
    "decolonizingcommunitypsychologybysupportingin": ("McNamara", "2018", ["decolonizing", "indigenous", "community"]),
    "indigenousculturalandcrossculturalpsychologya": ("Kim", "2000", ["indigenous", "cross", "cultural", "epistemology"]),
    "insurrectionsofindigenousknowledgesdebatingc": ("Bansal", "2022", ["insurrections", "indigenous", "critical"]),
    "fromindigenouspsychologiestocrossindigenouspsy": ("PePua", "2020", ["indigenous", "cross", "global"]),
    "indigenizingpsychology": ("Adolfsson", "2025", ["indigenizing", "ecological", "indigenous"]),

    # --- Title-only variants (파일명에 저자/연도 없는 경우) ---
    # HUNT-005
    "natureandorganizationofindividualdifferencesine": ("Miyake", "2012", ["nature", "organization", "individual", "differences", "EF"]),
    "unityanddiversityofexecutivefunctionsanetworka": ("Karr", "2022", ["network", "approach", "life", "span"]),
    "crosscountrybrazilandiraninvarianceoffractiona": ("Segura", "2023", ["Brazil", "Iran", "invariance"]),
    "rolebilingualinteractionalcontextspredictingin": ("Hartanto", "2020", ["bilingual", "interactional", "context"]),
    "factoranalyticevidencefortthecomplexityofthedel": ("McFarland", "2020", ["DKEFS", "factor", "complexity"]),
    "factorstructureofexecutivefunctionsmeasuredwit": ("Loffler", "2025", ["ERP", "factor", "structure", "EF"]),
    "latentvariableapproachtoexecutivecontrolinheal": ("AdroverRoig", "2012", ["latent", "variable", "healthy", "ageing"]),
    "neuereforexecutivefunctionresearchonthetransi": ("Zink", "2020", ["distributed", "EF", "centralized"]),
    "factoranalyticevidenceforthecomplexityofthedel": ("McFarland", "2020", ["DKEFS", "factor", "complexity"]),

    # HUNT-010
    "commonfactorofexecutivefunctionsmeasuresnothi": ("Loffler", "2024", ["common", "factor", "speed", "uptake"]),
    "adversityisassociatedwithlowergeneralprocessin": ("Vermeent", "2025", ["adversity", "processing", "speed", "EF"]),
    "processingspeedworkingmemoryandexecutivefuncti": ("Frischkorn", "2019", ["processing", "speed", "WM", "intelligence"]),
    "integratingtheswitchinginhibitionandupdatingmo": ("Jewsbury", "2016", ["CHC", "switching", "inhibition", "updating"]),
    "genomewideassociationstudyshowsthatexecutivefu": ("Hatoum", "2022", ["GWAS", "GABAergic", "cEF"]),
    "roleofprefrontalcortexincognitivecontrolandex": ("Friedman", "2021", ["PFC", "cognitive", "control", "EF"]),

    # HUNT-012
    "developmentofhotandcoolexecutivefunctionduring": ("Prencipe", "2011", ["hot", "cool", "EF", "adolescence"]),
    "componentsofsocioeconomicstatusdifferentiallyp": ("Demko", "2025", ["SES", "cool", "hot", "EF"]),
    "evaluatingthedistinctionbetweencoolandhotexecu": ("Moriguchi", "2023", ["evaluating", "distinction", "cool", "hot"]),
    "hotandcoolexecutivefunctionsinadolescencedevelo": ("Poon", "2018", ["hot", "cool", "adolescence"]),
    "predictorsofexecutivefunctionamong2yearoldsfro": ("Nimmapirat", "2023", ["Thai", "2", "year", "olds", "EF"]),
    "executivefunctionandpsychopathologyaneurodevelop": ("Zelazo", "2020", ["EF", "psychopathology", "neurodevelopmental"]),

    # HUNT-015
    "selfdeterminationtheoryandthefacilitationofint": ("Ryan", "2000", ["SDT", "intrinsic", "motivation"]),
    "selfdeterminationtheoryamacrotheoryofhumanmoti": ("Deci", "2008", ["SDT", "macrotheory", "motivation"]),
    "selfdeterminationtheoryappliedtophysicaleducati": ("Vasconcellos", "2020", ["SDT", "physical", "education", "meta"]),
    "testingacontinuumstructureofselfdeterminedmoti": ("Howard", "2017", ["continuum", "SDT", "meta", "analysis"]),
    "studentmotivationandassociatedoutcomesametaana": ("Howard", "2021", ["student", "motivation", "SDT", "meta"]),
    "pathwaystostudentmotivationametaanalysisofante": ("Bureau", "2021", ["pathways", "motivation", "autonomous"]),
    "applyingselfdeterminationtheorytoeducationregu": ("Guay", "2021", ["SDT", "education", "regulation"]),
    "applyingselfdeterminationtheorytoeducationalpra": ("Niemiec", "2009", ["SDT", "autonomy", "competence", "classroom"]),
    "intrinsicandextrinsicmotivationfromaselfdeterm": ("Ryan", "2020", ["intrinsic", "extrinsic", "SDT", "education"]),
    "twelvetipstostimulateintrinsicmotivationinstude": ("Kusurkar", "2011", ["tips", "intrinsic", "autonomy", "SDT"]),

    # HUNT-016
    "measurementofselfregulationinearlychildhoodrela": ("Lin", "2019", ["measurement", "EC", "EF"]),
    "selfregulationinelementaryschooldoteacherrepor": ("Weiss", "2023", ["elementary", "EC", "EF", "codevelop"]),
    "selfregulationinpreschoolchildrenfactorstructur": ("Kalin", "2021", ["preschool", "EC", "EF", "factor"]),

    # HUNT-017
    "dynamicfieldtheoryofexecutivefunctionidentifyi": ("McCraw", "2024", ["DFT", "EF", "neurocognitive", "markers"]),
    "emergentexecutiveadynamicfieldtheoryofthedeve": ("BussSpencer", "2014", ["emergent", "DFT", "EF"]),
    "dimensionalchangecardsortdccsamethodofassessi": ("Zelazo", "2006", ["DCCS", "protocol", "EF"]),
    "reconcilingthecontextdependencyanddomaingene": ("Zelazo", "2022", ["reconciling", "context", "domain", "general"]),
    "reconcilingthecontextdependencyanddomaingener": ("Zelazo", "2022", ["reconciling", "context", "domain", "general"]),

    # HUNT-020
    "developmentofexecutivefunctionmechanismsofchan": ("Ibbotson", "2023", ["mechanisms", "functional", "pressures"]),
    "consideringrolesofexecutivefunctionsinthescien": ("Cartwright", "2024", ["reading", "EF", "meta", "analysis"]),
    "whydoesntexecutivefunctiontrainingimproveacad": ("Niebaum", "2022", ["EF", "training", "contextual"]),
    "executivefunctionsinsocialcontextimplicationsf": ("Munakata", "2021", ["EF", "social", "context"]),

    # HUNT-034
    "verbalregulationofmotorbehaviorsovietresearcha": ("Wozniak", "1972", ["verbal", "regulation", "motor", "Soviet"]),
    "scopeandperspectivesofneuroimagingandneurostim": ("Panikratova", "2022", ["neuroimaging", "Luria", "Vygotsky"]),

    # HUNT-035
    "5makebelieveplaywellspringfordevelopmentofsel": ("Berk", "2006", ["make", "believe", "self", "regulation"]),
    "makebelieveplaywellspringfordevelopmentofself": ("Berk", "2006", ["make", "believe", "self", "regulation"]),
    "rolemakebelieveplayinthedevelopmentofexecutive": ("Berk", "2013", ["make", "believe", "EF", "children"]),
    "engagementinsocialpretendplaypredictspreschool": ("White", "2021", ["pretend", "play", "EF", "gains"]),
    "examiningtherelationbetweenadultscaffoldingofm": ("Duval", "2023", ["adult", "scaffolding", "make", "believe"]),
    "playandselfregulationessonsfrom6ygotsky": ("Bodrova", "2013", ["play", "self", "regulation", "Vygotsky"]),

    # HUNT-036
    "insurrectionsofindigenousknowledgesdebatingcr": ("Bansal", "2022", ["insurrections", "indigenous", "critical"]),

    # Fallback 보강 (umlaut·특수문자 포함 파일)
    "aneweraforexecutivefunctionresearchonthetrans": ("Zink", "2020", ["distributed", "EF", "centralized"]),
    "neweraforexecutivefunctionresearchonthetransi": ("Zink", "2020", ["distributed", "EF", "centralized"]),
    "doebelandmuller20233thefutureofresearchonex": ("Doebel", "2023", ["future", "research", "EF"]),
    "doebelandmller2023thefutureofresearchonexec": ("Doebel", "2023", ["future", "research", "EF"]),
    "doebelandmllerthefutureofresearchonexecutive": ("Doebel", "2023", ["future", "research", "EF"]),
    "gartnerandstrobel2021individualdifferencesini": ("Gartner", "2021", ["individual", "differences", "inhibitory"]),
    "grtnerandstrobel2021individualdifferencesini": ("Gartner", "2021", ["individual", "differences", "inhibitory"]),
    "muelletal2012testretestreliabilityandpractice": ("Muller", "2012", ["test", "retest", "reliability", "EF"]),
    "mlleretal2012testretestreliabilityandpractice": ("Muller", "2012", ["test", "retest", "reliability", "EF"]),
    "vandersluisetal2007executivefunctioninginchil": ("VanDerSluis", "2007", ["EF", "reasoning", "reading", "arithmetic"]),
    "yangezetal2024insearchofbetterpracticeinexe": ("Yanguez", "2024", ["better", "practice", "EF", "assessment"]),
    "yanguezetal2024insearchofbetterpracticeinexe": ("Yanguez", "2024", ["better", "practice", "EF", "assessment"]),

    # Misc (HUNT 외 수동 추가)
    "buss and kerr german dimensional attention as a mechanism": ("Buss", "2019", ["dimensional", "attention", "EF"]),
    "bussankerrgermandimensionalattentionasamechan": ("Buss", "2019", ["dimensional", "attention", "EF"]),
    "carriedoetalagerelatedchangeininhibitoryproc": ("Carriedo", "2025", ["age", "inhibitory", "WM", "speed"]),
    "causseetalmentalworkloadandneuralefficiencyqua": ("Causse", "2017", ["workload", "neural", "efficiency", "fNIRS"]),
    "chevalierthedevelopmentofexecutivefunctiontowar": ("Chevalier", "2015", ["EF", "coordination", "control"]),
    "childdevperspectives2015chevalierthedevelopme": ("Chevalier", "2015", ["EF", "coordination", "control"]),
    "cognitivecapacitylimitationsandneedforcognitio": ("Kruglanski", "2020", ["cognitive", "capacity", "need", "cognition"]),
    "diamondexecutivefunctions": ("Diamond", "2013", ["EF", "review"]),
    "doebelandlillardhowdoesplayfosterdevelopmenta": ("Doebel", "2023", ["play", "EF", "perspective"]),
    "doebelandmullerthefutureofresearchonexecutive": ("Doebel", "2023", ["future", "research", "EF"]),
    "ecclesandwigfieldfromexpectancyvaluetheoryto": ("Eccles", "2020", ["expectancy", "value", "theory"]),
    "friedmanresearchonindividualdifferencesinexec": ("Friedman", "2016", ["individual", "differences", "EF", "bilingual"]),
    "gaoetalenhancingbrainplasticityfunctionalnea": ("Gao", "2025", ["brain", "plasticity", "fNIRS", "WM"]),
    "gartnerandstrobelindividualdifferencesinininhib": ("Gartner", "2021", ["individual", "differences", "inhibitory"]),
    "grundetalwhenislearningeffortfulscrutinizing": ("Grund", "2024", ["learning", "effortful", "mental", "effort"]),
    "haithandkrakauerthemultipleeffectsofpracticesk": ("Haith", "2018", ["practice", "skill", "habit", "cognitive"]),
    "hedgeetalthereliabilityparadoxwhyrobustcognit": ("Hedge", "2018", ["reliability", "paradox", "cognitive"]),
    "howardetalchallengingsocioeconomicstatusacros": ("Howard", "2020", ["SES", "cross", "cultural", "EF"]),
    "jansmaetalfunctionalanatomicalcorrelatesofcon": ("Jansma", "2001", ["controlled", "automatic", "processing"]),
    "jinetalexternalrewardsandpositivestimulipromo": ("Jin", "2020", ["rewards", "stimuli", "cognitive", "control"]),
    "jukesetalprinciplesforadaptingassessmentsofex": ("Jukes", "2024", ["adapting", "EF", "cultural", "contexts"]),
    "karretaltheunityanddiversityofexecutivefunctio": ("Karr", "2018", ["unity", "diversity", "EF", "meta"]),
    "kassaietalametaanalysisoftheexperimentalevide": ("Kassai", "2019", ["transfer", "EF", "children", "meta"]),
    "metinetaladhdperformancereflectsinefficientbut": ("Metin", "2013", ["ADHD", "diffusion", "processing"]),
    "michaeletalstabilityofindividualdifferencesin": ("Michel", "2025", ["stability", "individual", "EF", "kindergarten"]),
    "munakataandmichaelsonexecutivefunctionsinsoci": ("Munakata", "2021", ["EF", "social", "context"]),
    "munakataetalwhatsnextadvancesandchallengesi": ("Munakata", "2023", ["environmental", "predictability", "EF"]),
    "mulleretaltestretestreliabilityandpracticeeff": ("Muller", "2012", ["test", "retest", "reliability", "EF"]),
    "niebaumetaladaptivehabitsunderstandingexecuti": ("Niebaum", "2025", ["adaptive", "habits", "EF"]),
    "nyongesaetalassessingexecutivefunctioninadoles": ("Nyongesa", "2019", ["adolescence", "EF", "scoping", "measures"]),
    "paapandsawitheroleoftestretestreliabilityinm": ("Paap", "2016", ["test", "retest", "reliability", "EF"]),
    "reymermetetalneithermeasurementerrornorspeeda": ("ReyMermet", "2025", ["measurement", "attention", "control"]),
    "shieldsandyonelinasevidenceforresponseinhibit": ("Shields", "2025", ["response", "inhibition", "common", "EF"]),
    "slotetalpreschoolerscognitiveandemotionalselfr": ("Slot", "2017", ["preschoolers", "pretend", "play", "EF"]),
    "snydermajordepressivedisorderisassociatedwithb": ("Snyder", "2013", ["depression", "EF", "meta"]),
    "spenceretalintegratingattentionworkingmemory": ("Spencer", "2025", ["WOLVES", "DFT", "EF", "integrating"]),
    "steinbeisarationalaccountofcognitivecontrolde": ("Steinbeis", "2023", ["rational", "cognitive", "control", "childhood"]),
    "vandersluisetalexecutivefunctioninginchildren": ("VanDerSluis", "2007", ["EF", "reasoning", "reading", "arithmetic"]),
    "westbrooketalwhatisthesubjectivecostofcognit": ("Westbrook", "2013", ["subjective", "cost", "cognitive", "effort"]),
    "westbrooketalthesubjectivevalueofcognitiveeff": ("Westbrook", "2019", ["subjective", "value", "cognitive", "effort"]),
    "willoughbyandblairtestretestreliabilityofanew": ("Willoughby", "2011", ["test", "retest", "reliability", "EF", "early"]),
    "willoughbyetalmeasuringexecutivefunctioninearl": ("Willoughby", "2013", ["measuring", "EF", "early", "childhood"]),
    "yangüezetalinsearchofbetterpracticeinexecutiv": ("Yanguez", "2024", ["better", "practice", "EF", "assessment"]),
}


def _candidate_keys(stem: str) -> list[str]:
    """여러 방식의 key 후보를 생성해 매핑 시도 확률 향상."""
    base = re.sub(r"^\d+\s+", "", stem)  # "5 Title" → "Title"
    # Raw key
    k1 = re.sub(r"[^a-z0-9]+", "", base.lower())[:50]
    # "The " 같은 관사 제거
    k2 = re.sub(r"[^a-z0-9]+", "", re.sub(r"^(the|a|an)\s+", "", base, flags=re.IGNORECASE).lower())[:50]
    # "Author - YYYY - Title" → Title만
    m = re.match(r"^[^-]+-\s*\d{4}\s*-\s*(.+)$", base)
    k3 = re.sub(r"[^a-z0-9]+", "", m.group(1).lower())[:50] if m else ""
    return [k for k in (k1, k2, k3) if k]


def normalize_filename(pdf_path: Path) -> dict:
    """반환: {'new_name': 'Author_Year_keyword1_keyword2.pdf', 'author':..., 'year':..., 'title':..., 'pages':...}"""
    fname = pdf_path.name
    stem = pdf_path.stem

    # 1순위: KNOWN_MAPPING (정확 매칭 + 보수적 prefix 매칭)
    cands = _candidate_keys(stem)
    # (a) 정확 매칭
    for cand in cands:
        if cand in KNOWN_MAPPING:
            author, year, kw = KNOWN_MAPPING[cand]
            short = "_".join(kw[:5])
            return {"new_name": f"{author}_{year}_{short}.pdf", "author": author,
                    "year": year, "title": stem, "source": "known_mapping"}
    # (b) prefix 매칭 — 최소 45자 공통 전제 (너무 짧으면 오매칭)
    MIN_PREFIX = 45
    for cand in cands:
        if len(cand) < MIN_PREFIX:
            continue
        for mkey, (author, year, kw) in KNOWN_MAPPING.items():
            if len(mkey) < MIN_PREFIX:
                continue
            common_len = min(len(cand), len(mkey))
            if common_len >= MIN_PREFIX and cand[:common_len] == mkey[:common_len]:
                short = "_".join(kw[:5])
                return {"new_name": f"{author}_{year}_{short}.pdf", "author": author,
                        "year": year, "title": stem, "source": "known_mapping"}

    # 2순위: 파일명 패턴 파싱
    parsed = parse_from_filename(fname)
    if parsed:
        author = parsed["author"] or "Unknown"
        year = parsed["year"]
        kw = title_keywords(parsed["title"], max_words=5)
        short = "_".join(kw) if kw else "untitled"
        new_name = f"{author}_{year}_{short}.pdf"
        return {"new_name": new_name, "author": author, "year": year,
                "title": parsed["title"], "source": "filename_pattern"}

    # 3순위: PDF 메타데이터
    meta = extract_pdf_metadata(pdf_path)
    if meta["title"] and meta["author"]:
        author = parse_author_first(meta["author"])
        year_match = re.search(r"(19|20)\d{2}", fname + " " + meta.get("title", ""))
        year = year_match.group(0) if year_match else "nodate"
        kw = title_keywords(meta["title"], max_words=5)
        short = "_".join(kw) if kw else "untitled"
        new_name = f"{author}_{year}_{short}.pdf"
        return {"new_name": new_name, "author": author, "year": year,
                "title": meta["title"], "pages": meta.get("pages", 0), "source": "pdf_metadata"}

    # fallback: 제목에서 추정
    kw = title_keywords(stem, max_words=6)
    short = "_".join(kw) if kw else re.sub(r"[^a-zA-Z0-9]+", "_", stem)[:50]
    return {"new_name": f"Unknown_nodate_{short}.pdf", "author": "Unknown",
            "year": "nodate", "title": stem, "source": "fallback"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 normalize_filename.py <pdf_path>")
        sys.exit(1)
    p = Path(sys.argv[1])
    result = normalize_filename(p)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
