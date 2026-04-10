# training_data/master_annotations.py
# Add new examples from each document you process.
# Format: (text, {"entities": [(start, end, "LABEL"), ...]})

TRAIN_DATA = [

    # ══════════════════════════════════════════════
    # FROM: 156812025_2026-02-10.pdf
    # Suo Moto WP (Crl) No. 1/2025
    # ══════════════════════════════════════════════

    # -- Header block --
    ("IN THE SUPREME COURT OF INDIA\nCRIMINAL ORIGINAL/APPELLATE JURISDICTION",
     {"entities": [(7, 30, "COURT_NAME"), (31, 71, "JURISDICTION")]}),

    ("Suo Moto Writ Petition (Criminal) No. 1 / 2025",
     {"entities": [(0, 47, "CASE_NUMBER"), (0, 33, "CASE_TYPE")]}),

    ("Criminal Revision No. 1449/2024",
     {"entities": [(0, 31, "CASE_NUMBER"), (0, 18, "CASE_TYPE")]}),

    ("Diary No. 15692/2025",
     {"entities": [(0, 20, "CASE_NUMBER")]}),

    ("Diary No. 21813/2025",
     {"entities": [(0, 20, "CASE_NUMBER")]}),

    # -- Judge byline (teaches: "J." is suffix cue, NOT part of name) --
    ("SURYA KANT, J.",
     {"entities": [(0, 10, "JUDGE")]}),

    # -- CJI title reference (teaches: title-as-entity when name absent) --
    ("in accordance with the directions of Hon'ble the Chief Justice of India",
     {"entities": [(48, 71, "JUDGE")]}),

    # -- Advocate identification (teaches: role suffix disambiguates) --
    ("Ms. Shobha Gupta, Senior Advocate, through its Founder President",
     {"entities": [(0, 15, "SENIOR_ADVOCATE"), (17, 33, "SENIOR_ADVOCATE")]}),

    # -- Multi-advocate sentence (teaches: list disambiguation) --
    ("We have heard Ms. Shobha Gupta, learned Senior Counsel, Mr. H.S. Phoolka, learned Senior Counsel, representing the Delhi-based NGO and the complainant-mother, and Mr. Sharan Dev Singh Thakur, learned Senior Additional Advocate General for the State of Uttar Pradesh.",
     {"entities": [
         (14, 30,  "SENIOR_ADVOCATE"),
         (40, 54,  "SENIOR_ADVOCATE"),
         (56, 73,  "SENIOR_ADVOCATE"),
         (83, 97,  "SENIOR_ADVOCATE"),
         (163, 190, "GOVERNMENT_COUNSEL"),
         (200, 235, "GOVERNMENT_COUNSEL"),
         (244, 264, "STATE"),
     ]}),

    # -- Law cluster (teaches: SECTION + ACT_NAME + combined LEGAL_PROVISION) --
    ("Section 376 of the Indian Penal Code, 1860 read with Section 18 of the Protection of Children from Sexual Offences Act, 2012",
     {"entities": [
         (0,   11,  "SECTION"),
         (19,  43,  "ACT_NAME"),
         (53,  63,  "SECTION"),
         (71,  125, "ACT_NAME"),
     ]}),

    ("Section 354B of the IPC read with Sections 9 and 10 of the POCSO Act",
     {"entities": [
         (0,  13, "SECTION"),
         (20, 23, "ACT_NAME"),
         (34, 50, "SECTION"),
         (59, 68, "ACT_NAME"),
     ]}),

    ("Section 376 read with Section 511 of the IPC and Section 18 of the POCSO Act",
     {"entities": [
         (0,  11, "SECTION"),
         (22, 33, "SECTION"),
         (41, 44, "ACT_NAME"),
         (49, 59, "SECTION"),
         (67, 76, "ACT_NAME"),
     ]}),

    ("Section 156(3) of the Code of Criminal Procedure, 1973",
     {"entities": [(0, 14, "SECTION"), (22, 55, "ACT_NAME")]}),

    # -- Precedent + citation --
    ("State of Madhya Pradesh v. Mahendra alias Golu, reported in (2022) 12 SCC 442",
     {"entities": [(0, 46, "PRECEDENT_CASE"), (61, 77, "CITATION")]}),

    # -- Lower court + dates --
    ("a judgment dated 17.03.2025 passed by a Single Judge of the High Court of Judicature at Allahabad",
     {"entities": [
         (17, 27, "JUDGMENT_DATE"),
         (60, 98, "COURT_NAME"),
         (60, 98, "LOWER_COURT"),
     ]}),

    ("order of summons dated 26.03.2023 issued by the Special Judge (POCSO), Kasganj",
     {"entities": [
         (22, 32, "ORDER_DATE"),
         (49, 79, "LOWER_COURT"),
         (72, 79, "COURT_LOCATION"),
     ]}),

    # -- Parties --
    ("Notice was issued to the Union of India, the State of Uttar Pradesh",
     {"entities": [
         (25, 39, "RESPONDENT"),
         (45, 67, "RESPONDENT"),
         (45, 67, "STATE"),
     ]}),

    ("the complainant in Complaint Case No. 23/2022, who is the mother of the minor victim",
     {"entities": [
         (4,  14, "COMPLAINANT"),
         (18, 45, "CASE_NUMBER"),
         (73, 84, "VICTIM"),
     ]}),

    # -- Interim + final orders --
    ("the observations of the High Court in paragraphs 21, 24, and 26 of the impugned order were stayed",
     {"entities": [
         (72, 85, "IMPUGNED_ORDER"),
         (92, 98, "INTERIM_ORDER"),
     ]}),

    ("the instant Criminal Appeals, arising out of Diary Nos. 15692 and 21813/2025, are allowed",
     {"entities": [
         (12, 28, "CASE_TYPE"),
         (45, 76, "CASE_NUMBER"),
         (82, 89, "FINAL_VERDICT"),
     ]}),

    ("The impugned judgment dated 17.03.2025 is set aside",
     {"entities": [
         (27, 37, "JUDGMENT_DATE"),
         (41, 50, "RELIEF_GRANTED"),
     ]}),

    ("the original summons order dated 23.06.2023 passed by the Special Judge (POCSO), Kasganj is restored",
     {"entities": [
         (32, 42, "ORDER_DATE"),
         (57, 88, "LOWER_COURT"),
         (91, 100, "DIRECTION"),
     ]}),

    # -- Committee / ORG (teaches: "X as Chairperson" suppression) --
    ("we request the National Judicial Academy, Bhopal, through its Director, Justice Aniruddha Bose, former Judge of this Court",
     {"entities": [
         (15, 48, "ORG"),
         (42, 48, "COURT_LOCATION"),
         (72, 94, "JUDGE"),
         # "former Judge of this Court" → context, not a new entity
     ]}),

    ("The Committee of Experts shall be presided over by Justice Bose as Chairperson",
     {"entities": [
         (4,  24, "ORG"),
         (51, 63, "JUDGE"),
         # "as Chairperson" → SUPPRESSED — predicate, not entity
     ]}),

    # -- Signature block (teaches: names in parens after J./CJI are JUDGEs) --
    ("CJI\n(SURYA KANT)\nJ.\n(JOYMALYA BAGCHI)\nJ.\n(N. V. ANJARIA)\nNEW DELHI;\nFEBRUARY 10, 2026",
     {"entities": [
         (0,  88, "SIGNATURE_BLOCK"),
         (4,  14, "JUDGE"),
         (19, 35, "JUDGE"),
         (40, 51, "JUDGE"),
         (53, 62, "COURT_LOCATION"),
         (64, 81, "JUDGMENT_DATE"),
     ]}),

    # -- Document structure --
    ("A. RE: IMPUGNED JUDGMENT DATED 17.03.2025",
     {"entities": [(0, 41, "SECTION_HEADER")]}),

    ("B. RE: BROADER ISSUE OF GUIDELINES FOR INCULCATING SENSITIVITY AND COMPASSION INTO JUDICIAL APPROACH",
     {"entities": [(0, 101, "SECTION_HEADER")]}),

    # ══════════════════════════════════════════════
    # GENERALISATION EXAMPLES
    # (teach patterns that appear across ALL documents)
    # ══════════════════════════════════════════════

    # Different case number formats
    ("Writ Petition (Civil) No. 494 of 2012",
     {"entities": [(0, 37, "CASE_NUMBER"), (0, 21, "CASE_TYPE")]}),

    ("Criminal Appeal No. 1234 of 2023",
     {"entities": [(0, 32, "CASE_NUMBER"), (0, 15, "CASE_TYPE")]}),

    ("SLP (Criminal) No. 5678 of 2024",
     {"entities": [(0, 31, "CASE_NUMBER"), (0, 14, "CASE_TYPE")]}),

    ("Transfer Petition (Civil) No. 100 of 2022",
     {"entities": [(0, 41, "CASE_NUMBER")]}),

    # Different judge formats
    ("SANJIV KHANNA, J.",
     {"entities": [(0, 13, "JUDGE")]}),

    ("B.R. GAVAI, CJI",
     {"entities": [(0, 10, "JUDGE")]}),

    ("Hon'ble Mr. Justice Abhay S. Oka",
     {"entities": [(0, 32, "JUDGE")]}),

    ("Coram: Sanjiv Khanna, C.J.I. and Sanjay Kumar, J.",
     {"entities": [
         (0,  5,  "CORAM"),
         (7,  28, "JUDGE"),
         (33, 46, "JUDGE"),
     ]}),

    # Different court names
    ("High Court of Judicature at Bombay",
     {"entities": [(0, 34, "COURT_NAME")]}),

    ("the Delhi High Court",
     {"entities": [(4, 20, "COURT_NAME")]}),

    ("the Madras High Court",
     {"entities": [(4, 21, "COURT_NAME")]}),

    ("Sessions Court, Gautam Buddha Nagar",
     {"entities": [(0, 35, "COURT_NAME"), (0, 35, "LOWER_COURT")]}),

    ("Special Court under the POCSO Act, Mumbai",
     {"entities": [(0, 41, "LOWER_COURT"), (33, 41, "COURT_LOCATION")]}),

    # Different advocate patterns
    ("Mr. Kapil Sibal, Senior Advocate, appearing for the Petitioner",
     {"entities": [(0, 15, "SENIOR_ADVOCATE"), (17, 32, "SENIOR_ADVOCATE")]}),

    ("learned Amicus Curiae, Ms. Indira Jaising, Senior Advocate",
     {"entities": [(25, 41, "SENIOR_ADVOCATE"), (43, 58, "SENIOR_ADVOCATE")]}),

    ("Mr. Vikramjit Banerjee, Additional Solicitor General of India",
     {"entities": [(0, 22, "GOVERNMENT_COUNSEL"), (24, 61, "GOVERNMENT_COUNSEL")]}),

    # FIR + police station patterns
    ("FIR No. 128/2023 registered at Kotwali Police Station, Varanasi",
     {"entities": [
         (0,  16, "FIR_NUMBER"),
         (31, 63, "POLICE_STATION"),
         (55, 63, "COURT_LOCATION"),
     ]}),

    ("Crime No. 45/2024 under Section 302 IPC",
     {"entities": [
         (0,  17, "FIR_NUMBER"),
         (24, 35, "SECTION"),
         (36, 39, "ACT_NAME"),
     ]}),

    # Bail patterns
    ("The Accused is in judicial custody. Bail application rejected.",
     {"entities": [
         (4,  11, "ACCUSED"),
         (36, 52, "BAIL_STATUS"),
         (53, 61, "BAIL_STATUS"),
     ]}),

    ("Anticipatory bail granted by the Sessions Court vide order dated 15.04.2024",
     {"entities": [
         (0,  18, "BAIL_STATUS"),
         (33, 47, "LOWER_COURT"),
         (65, 75, "ORDER_DATE"),
     ]}),

    # Evidence and witnesses
    ("PW-1, Dr. Rakesh Sharma, Medical Officer, deposed that the victim was examined",
     {"entities": [
         (0,  22, "WITNESS"),
         (63, 69, "VICTIM"),
     ]}),

    ("The forensic report and CCTV footage corroborate the prosecution case",
     {"entities": [
         (4,  19, "EVIDENCE"),
         (24, 36, "EVIDENCE"),
     ]}),

    # Section header patterns
    ("I. BACKGROUND FACTS",
     {"entities": [(0, 19, "SECTION_HEADER")]}),

    ("II. ISSUES FOR CONSIDERATION",
     {"entities": [(0, 28, "SECTION_HEADER")]}),

    ("III. ANALYSIS AND FINDINGS",
     {"entities": [(0, 26, "SECTION_HEADER")]}),

    # Paragraph numbers
    ("1. The present Writ Petition challenges the constitutional validity",
     {"entities": [(0, 2, "PARAGRAPH_NUMBER")]}),

    ("22. Having heard the learned counsel for the parties",
     {"entities": [(0, 3, "PARAGRAPH_NUMBER")]}),
]