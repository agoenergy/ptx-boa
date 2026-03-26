"""DO NOT EDIT (created by classes/_update.py)."""

import ptxboa.classes.base


class PtxboaParameters:
    CALOR = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CALOR",
        code="CALOR",
        name="calorific values",
        template_class_name="PtxboaParameter",
    )
    CAPEX = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CAPEX",
        code="CAPEX",
        name="CAPEX",
        template_class_name="PtxboaParameter",
    )
    CAP_T = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CAP_T",
        code="CAP-T",
        name="transport capacity",
        template_class_name="PtxboaParameter",
    )
    CBOUND = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CBOUND",
        code="CBOUND",
        name="C bound in product",
        template_class_name="PtxboaParameter",
    )
    CH4SHARE = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CH4SHARE",
        code="CH4SHARE",
        name="methane share",
        template_class_name="PtxboaParameter",
    )
    CO2CPT_R = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CO2CPT_R",
        code="CO2CPT-R",
        name="capture rate by flow",
        template_class_name="PtxboaParameter",
    )
    CO2CPT_S = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CO2CPT_S",
        code="CO2CPT-S",
        name="CO2 for capture share",
        template_class_name="PtxboaParameter",
    )
    CONV = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CONV",
        code="CONV",
        name="conversion factors",
        template_class_name="PtxboaParameter",
    )
    CONV_OT = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_CONV_OT",
        code="CONV-OT",
        name="conversion factors (other fuel, transport)",
        template_class_name="PtxboaParameter",
    )
    DST_S_D = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_DST_S_D",
        code="DST-S-D",
        name="shipping distance",
        template_class_name="PtxboaParameter",
    )
    DST_S_DP = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_DST_S_DP",
        code="DST-S-DP",
        name="pipeline distance",
        template_class_name="PtxboaParameter",
    )
    EF_E = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_EF_E",
        code="EF_E",
        name="emission factor for emission balance",
        template_class_name="PtxboaParameter",
    )
    EF_M = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_EF_M",
        code="EF_M",
        name="emission factor for mass balance",
        template_class_name="PtxboaParameter",
    )
    EFF = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_EFF",
        code="EFF",
        name="efficiency",
        template_class_name="PtxboaParameter",
    )
    FLH = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_FLH",
        code="FLH",
        name="full load hours",
        template_class_name="PtxboaParameter",
    )
    LIFETIME = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_LIFETIME",
        code="LIFETIME",
        name="lifetime / amortization period",
        template_class_name="PtxboaParameter",
    )
    LOSS = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_LOSS",
        code="LOSS",
        name="losses (own fuel)",
        template_class_name="PtxboaParameter",
    )
    LOSS_T = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_LOSS_T",
        code="LOSS-T",
        name="losses (own fuel, transport)",
        template_class_name="PtxboaParameter",
    )
    OPEX_F = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_OPEX_F",
        code="OPEX-F",
        name="OPEX (fix)",
        template_class_name="PtxboaParameter",
    )
    OPEX_O = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_OPEX_O",
        code="OPEX-O",
        name="OPEX (other variable)",
        template_class_name="PtxboaParameter",
    )
    OPEX_T = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_OPEX_T",
        code="OPEX-T",
        name="levelized costs",
        template_class_name="PtxboaParameter",
    )
    SEASHARE = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_SEASHARE",
        code="SEASHARE",
        name="sea share of pipeline distance",
        template_class_name="PtxboaParameter",
    )
    SPECCOST = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_SPECCOST",
        code="SPECCOST",
        name="specific costs",
        template_class_name="PtxboaParameter",
    )
    WACC = ptxboa.classes.base.PtxboaParameter._create_subclass(
        "PtxboaParameter_WACC",
        code="WACC",
        name="WACC",
        template_class_name="PtxboaParameter",
    )


class PtxboaFlows:
    B_DRI_S = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_B_DRI_S",
        code="B-DRI-S",
        name="Blue iron",
        template_class_name="PtxboaFlow",
    )
    BFUEL_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_BFUEL_L",
        code="BFUEL-L",
        name="bunker fuel",
        template_class_name="PtxboaFlow",
    )
    CH3OH_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_CH3OH_L",
        code="CH3OH-L",
        name="methanol (liquid)",
        template_class_name="PtxboaFlow",
    )
    CH4_G = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_CH4_G",
        code="CH4-G",
        name="methane (gas)",
        template_class_name="PtxboaFlow",
    )
    CH4_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_CH4_L",
        code="CH4-L",
        name="methane (liquid)",
        template_class_name="PtxboaFlow",
    )
    CHX_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_CHX_L",
        code="CHX-L",
        name="FT e-fuels",
        template_class_name="PtxboaFlow",
    )
    CO2_C = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_CO2_C",
        code="CO2-C",
        name="carbon dioxide (critical phase)",
        template_class_name="PtxboaFlow",
    )
    CO2_G = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_CO2_G",
        code="CO2-G",
        name="carbon dioxide",
        template_class_name="PtxboaFlow",
    )
    DIESEL_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_DIESEL_L",
        code="DIESEL-L",
        name="diesel (liquid)",
        template_class_name="PtxboaFlow",
    )
    DRI_S = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_DRI_S",
        code="DRI-S",
        name="Green iron",
        template_class_name="PtxboaFlow",
    )
    EL = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_EL", code="EL", name="electricity", template_class_name="PtxboaFlow"
    )
    H2_G = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_H2_G",
        code="H2-G",
        name="hydrogen (gas)",
        template_class_name="PtxboaFlow",
    )
    H2_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_H2_L",
        code="H2-L",
        name="hydrogen (liquid)",
        template_class_name="PtxboaFlow",
    )
    H2O_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_H2O_L", code="H2O-L", name="water", template_class_name="PtxboaFlow"
    )
    HEAT = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_HEAT", code="HEAT", name="heat", template_class_name="PtxboaFlow"
    )
    IOP_S = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_IOP_S",
        code="IOP-S",
        name="iron ore pellets",
        template_class_name="PtxboaFlow",
    )
    LOHC_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_LOHC_L",
        code="LOHC-L",
        name="hydrogen (LOHC)",
        template_class_name="PtxboaFlow",
    )
    N2_G = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_N2_G",
        code="N2-G",
        name="nitrogen",
        template_class_name="PtxboaFlow",
    )
    NG_G = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_NG_G",
        code="NG-G",
        name="natural gas (gasous)",
        template_class_name="PtxboaFlow",
    )
    NG_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_NG_L",
        code="NG-L",
        name="natural gas (liquid)",
        template_class_name="PtxboaFlow",
    )
    NH3_L = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_NH3_L",
        code="NH3-L",
        name="ammonia (liquid)",
        template_class_name="PtxboaFlow",
    )
    STL_S = ptxboa.classes.base.PtxboaFlow._create_subclass(
        "PtxboaFlow_STL_S",
        code="STL-S",
        name="crude steel",
        template_class_name="PtxboaFlow",
    )


class PtxboaRegions:
    ARE = ptxboa.classes.base.PtxboaRegion(code="ARE", name="United Arab Emirates")
    ARG = ptxboa.classes.base.PtxboaRegion(code="ARG", name="Argentina")
    ARG_BA = ptxboa.classes.base.PtxboaRegion(
        code="ARG-BA", name="Argentina (Buenos Aires)"
    )
    ARG_CAT = ptxboa.classes.base.PtxboaRegion(
        code="ARG-CAT", name="Argentina (Catamarca)"
    )
    ARG_CBA = ptxboa.classes.base.PtxboaRegion(
        code="ARG-CBA", name="Argentina (Autonomous City of Buenos Aires)"
    )
    ARG_CHA = ptxboa.classes.base.PtxboaRegion(code="ARG-CHA", name="Argentina (Chaco)")
    ARG_CHU = ptxboa.classes.base.PtxboaRegion(
        code="ARG-CHU", name="Argentina (Chubut)"
    )
    ARG_COR = ptxboa.classes.base.PtxboaRegion(
        code="ARG-COR", name="Argentina (Corrientes)"
    )
    ARG_CRB = ptxboa.classes.base.PtxboaRegion(
        code="ARG-CRB", name="Argentina (Córdoba)"
    )
    ARG_CRU = ptxboa.classes.base.PtxboaRegion(
        code="ARG-CRU", name="Argentina (Santa Cruz)"
    )
    ARG_EST = ptxboa.classes.base.PtxboaRegion(
        code="ARG-EST", name="Argentina (Santiago del Estero)"
    )
    ARG_FOR = ptxboa.classes.base.PtxboaRegion(
        code="ARG-FOR", name="Argentina (Formosa)"
    )
    ARG_FUE = ptxboa.classes.base.PtxboaRegion(
        code="ARG-FUE",
        name="Argentina (Tierra del Fuego, Antártida e Islas del Atlántico Sur)",
    )
    ARG_JUJ = ptxboa.classes.base.PtxboaRegion(code="ARG-JUJ", name="Argentina (Jujuy)")
    ARG_LAR = ptxboa.classes.base.PtxboaRegion(
        code="ARG-LAR", name="Argentina (La Rioja)"
    )
    ARG_MEN = ptxboa.classes.base.PtxboaRegion(
        code="ARG-MEN", name="Argentina (Mendoza)"
    )
    ARG_MIS = ptxboa.classes.base.PtxboaRegion(
        code="ARG-MIS", name="Argentina (Misiones)"
    )
    ARG_NEG = ptxboa.classes.base.PtxboaRegion(
        code="ARG-NEG", name="Argentina (Río Negro)"
    )
    ARG_NEU = ptxboa.classes.base.PtxboaRegion(
        code="ARG-NEU", name="Argentina (Neuquén)"
    )
    ARG_PAM = ptxboa.classes.base.PtxboaRegion(
        code="ARG-PAM", name="Argentina (La Pampa)"
    )
    ARG_RIO = ptxboa.classes.base.PtxboaRegion(
        code="ARG-RIO", name="Argentina (Entre Ríos)"
    )
    ARG_SAF = ptxboa.classes.base.PtxboaRegion(
        code="ARG-SAF", name="Argentina (Santa Fe)"
    )
    ARG_SAJ = ptxboa.classes.base.PtxboaRegion(
        code="ARG-SAJ", name="Argentina (San Juan)"
    )
    ARG_SAL = ptxboa.classes.base.PtxboaRegion(
        code="ARG-SAL", name="Argentina (San Luis)"
    )
    ARG_SAT = ptxboa.classes.base.PtxboaRegion(code="ARG-SAT", name="Argentina (Salta)")
    ARG_TUC = ptxboa.classes.base.PtxboaRegion(
        code="ARG-TUC", name="Argentina (Tucumán)"
    )
    AUS = ptxboa.classes.base.PtxboaRegion(code="AUS", name="Australia")
    BRA = ptxboa.classes.base.PtxboaRegion(code="BRA", name="Brazil")
    CHL = ptxboa.classes.base.PtxboaRegion(code="CHL", name="Chile")
    CHN = ptxboa.classes.base.PtxboaRegion(code="CHN", name="China")
    COL = ptxboa.classes.base.PtxboaRegion(code="COL", name="Colombia")
    CRI = ptxboa.classes.base.PtxboaRegion(code="CRI", name="Costa Rica")
    DEU = ptxboa.classes.base.PtxboaRegion(code="DEU", name="Germany")
    DNK = ptxboa.classes.base.PtxboaRegion(code="DNK", name="Denmark")
    DZA = ptxboa.classes.base.PtxboaRegion(code="DZA", name="Algeria")
    EGY = ptxboa.classes.base.PtxboaRegion(code="EGY", name="Egypt")
    ESP = ptxboa.classes.base.PtxboaRegion(code="ESP", name="Spain")
    FRA = ptxboa.classes.base.PtxboaRegion(code="FRA", name="France")
    IDN = ptxboa.classes.base.PtxboaRegion(code="IDN", name="Indonesia")
    IND = ptxboa.classes.base.PtxboaRegion(code="IND", name="India")
    JOR = ptxboa.classes.base.PtxboaRegion(code="JOR", name="Jordan")
    JPN = ptxboa.classes.base.PtxboaRegion(code="JPN", name="Japan")
    KAZ = ptxboa.classes.base.PtxboaRegion(code="KAZ", name="Kazakhstan")
    KEN = ptxboa.classes.base.PtxboaRegion(code="KEN", name="Kenya")
    KOR = ptxboa.classes.base.PtxboaRegion(code="KOR", name="South Korea")
    MAR = ptxboa.classes.base.PtxboaRegion(code="MAR", name="Morocco")
    MAR_BEN = ptxboa.classes.base.PtxboaRegion(
        code="MAR-BEN", name="Morocco (Béni Mellal-Khénifra)"
    )
    MAR_CAS = ptxboa.classes.base.PtxboaRegion(
        code="MAR-CAS", name="Morocco (Casablanca)"
    )
    MAR_DAK = ptxboa.classes.base.PtxboaRegion(
        code="MAR-DAK", name="Morocco (Dakhla-Oued Ed-Dahab)"
    )
    MAR_DRA = ptxboa.classes.base.PtxboaRegion(
        code="MAR-DRA", name="Morocco (Drâa-Tafilalet)"
    )
    MAR_FES = ptxboa.classes.base.PtxboaRegion(
        code="MAR-FES", name="Morocco (Fès-Meknès)"
    )
    MAR_GUE = ptxboa.classes.base.PtxboaRegion(
        code="MAR-GUE", name="Morocco (Guelmim-Oued Noun)"
    )
    MAR_LAA = ptxboa.classes.base.PtxboaRegion(
        code="MAR-LAA", name="Morocco (Laâyoune-Sakia El Hamra)"
    )
    MAR_LOR = ptxboa.classes.base.PtxboaRegion(
        code="MAR-LOR", name="Morocco (L´oriental)"
    )
    MAR_MAR = ptxboa.classes.base.PtxboaRegion(
        code="MAR-MAR", name="Morocco (Marrakech-Safi)"
    )
    MAR_RAB = ptxboa.classes.base.PtxboaRegion(
        code="MAR-RAB", name="Morocco (Rabat-Salé-Kénitra)"
    )
    MAR_SOU = ptxboa.classes.base.PtxboaRegion(
        code="MAR-SOU", name="Morocco (Souss-Massa)"
    )
    MAR_TAN = ptxboa.classes.base.PtxboaRegion(code="MAR-TAN", name="Morocco (Tangier)")
    MEX = ptxboa.classes.base.PtxboaRegion(code="MEX", name="Mexico")
    MRT = ptxboa.classes.base.PtxboaRegion(code="MRT", name="Mauritania")
    MYS = ptxboa.classes.base.PtxboaRegion(code="MYS", name="Malaysia")
    NAM = ptxboa.classes.base.PtxboaRegion(code="NAM", name="Namibia")
    NLD = ptxboa.classes.base.PtxboaRegion(code="NLD", name="Netherlands")
    NOR = ptxboa.classes.base.PtxboaRegion(code="NOR", name="Norway")
    OMN = ptxboa.classes.base.PtxboaRegion(code="OMN", name="Oman")
    PER = ptxboa.classes.base.PtxboaRegion(code="PER", name="Peru")
    PRT = ptxboa.classes.base.PtxboaRegion(code="PRT", name="Portugal")
    QAT = ptxboa.classes.base.PtxboaRegion(code="QAT", name="Qatar")
    RUS = ptxboa.classes.base.PtxboaRegion(code="RUS", name="Russia")
    SAU = ptxboa.classes.base.PtxboaRegion(code="SAU", name="Saudi Arabia")
    SWE = ptxboa.classes.base.PtxboaRegion(code="SWE", name="Sweden")
    THA = ptxboa.classes.base.PtxboaRegion(code="THA", name="Thailand")
    TUN = ptxboa.classes.base.PtxboaRegion(code="TUN", name="Tunisia")
    UKR = ptxboa.classes.base.PtxboaRegion(code="UKR", name="Ukraine")
    URY = ptxboa.classes.base.PtxboaRegion(code="URY", name="Uruguay")
    USA = ptxboa.classes.base.PtxboaRegion(code="USA", name="USA")
    VNM = ptxboa.classes.base.PtxboaRegion(code="VNM", name="Vietnam")
    ZAF = ptxboa.classes.base.PtxboaRegion(code="ZAF", name="South Africa")
    ZAF_EC = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-EC", name="South Africa (East Cape)"
    )
    ZAF_FRS = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-FRS", name="South Africa (Free State)"
    )
    ZAF_GAU = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-GAU", name="South Africa (Gauteng)"
    )
    ZAF_KWA = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-KWA", name="South Africa (KwaZulu-Natal)"
    )
    ZAF_LIM = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-LIM", name="South Africa (Limpopo)"
    )
    ZAF_MPU = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-MPU", name="South Africa (Mpumalanga)"
    )
    ZAF_NC = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-NC", name="South Africa (Northern Cape)"
    )
    ZAF_NW = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-NW", name="South Africa (North West)"
    )
    ZAF_WC = ptxboa.classes.base.PtxboaRegion(
        code="ZAF-WC", name="South Africa (Western Cape)"
    )


class PtxboaProcesss:
    AEL_EL = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_AEL_EL",
        code="AEL-EL",
        name="AEL electrolysis",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.EL,
        template_class_name="PtxboaProcess",
    )
    ATR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_ATR",
        code="ATR",
        name="Methane reconversion",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    ATR_91_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_ATR_91_B",
        code="ATR_91%#B",
        name="autothermal reformer with 91% carbon capture (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CCGT_CC_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CCGT_CC_B",
        code="CCGT-CC#B",
        name="Combined Cycle Gas Turbine with CCS (blue)",
        main_flow_type_out=PtxboaFlows.EL,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH3OH_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OH_S",
        code="CH3OH-S",
        name="Methanol ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.CH3OH_L,
        template_class_name="PtxboaProcess",
    )
    CH3OH_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OH_S_B",
        code="CH3OH-S#B",
        name="Methanol ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.CH3OH_L,
        template_class_name="PtxboaProcess",
    )
    CH3OH_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OH_SB",
        code="CH3OH-SB",
        name="Methanol ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.CH3OH_L,
        template_class_name="PtxboaProcess",
    )
    CH3OH_SB_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OH_SB_B",
        code="CH3OH-SB#B",
        name="Methanol ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.CH3OH_L,
        template_class_name="PtxboaProcess",
    )
    CH3OHSYC_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OHSYC_B",
        code="CH3OHSYC#B",
        name="Methanol Synthesis classic route with CCS (blue)",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH3OHSYN = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OHSYN",
        code="CH3OHSYN",
        name="Methanol Synthesis",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    CH3OHSYN_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH3OHSYN_B",
        code="CH3OHSYN#B",
        name="Methanol Synthesis (blue)",
        main_flow_type_out=PtxboaFlows.CH3OH_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    CH4_COMP = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_COMP",
        code="CH4-COMP",
        name="Methane compression",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    CH4_COMP_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_COMP_B",
        code="CH4-COMP#B",
        name="Methane compression (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH4_LIQ = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_LIQ",
        code="CH4-LIQ",
        name="Methane Liquefaction",
        main_flow_type_out=PtxboaFlows.CH4_L,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    CH4_LIQ_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_LIQ_B",
        code="CH4-LIQ#B",
        name="Methane Liquefaction (blue)",
        main_flow_type_out=PtxboaFlows.NG_L,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_L = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_L",
        code="CH4-P-L",
        name="Methane land pipeline new",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_L_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_L_B",
        code="CH4-P-L#B",
        name="Methane land pipeline new (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_LR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_LR",
        code="CH4-P-LR",
        name="Methane land pipeline retrofitted",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_LR_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_LR_B",
        code="CH4-P-LR#B",
        name="Methane land pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_S",
        code="CH4-P-S",
        name="Methane sea pipeline",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_S_B",
        code="CH4-P-S#B",
        name="Methane sea pipeline (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_SR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_SR",
        code="CH4-P-SR",
        name="Methane sea pipeline retrofitted",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.CH4_G,
        template_class_name="PtxboaProcess",
    )
    CH4_P_SR_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_P_SR_B",
        code="CH4-P-SR#B",
        name="Methane sea pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    CH4_RGAS = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_RGAS",
        code="CH4-RGAS",
        name="Methane Regasification",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.CH4_L,
        template_class_name="PtxboaProcess",
    )
    CH4_RGAS_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_RGAS_B",
        code="CH4-RGAS#B",
        name="Methane Regasification (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=PtxboaFlows.NG_L,
        template_class_name="PtxboaProcess",
    )
    CH4_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_S",
        code="CH4-S",
        name="LNG ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlows.CH4_L,
        main_flow_type_in=PtxboaFlows.CH4_L,
        template_class_name="PtxboaProcess",
    )
    CH4_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_S_B",
        code="CH4-S#B",
        name="LNG ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.NG_L,
        main_flow_type_in=PtxboaFlows.NG_L,
        template_class_name="PtxboaProcess",
    )
    CH4_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_SB",
        code="CH4-SB",
        name="LNG ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.CH4_L,
        main_flow_type_in=PtxboaFlows.CH4_L,
        template_class_name="PtxboaProcess",
    )
    CH4_SB_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4_SB_B",
        code="CH4-SB#B",
        name="LNG ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.NG_L,
        main_flow_type_in=PtxboaFlows.NG_L,
        template_class_name="PtxboaProcess",
    )
    CH4SYN = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CH4SYN",
        code="CH4SYN",
        name="Methane Synthesis",
        main_flow_type_out=PtxboaFlows.CH4_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    CO2_T_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_CO2_T_S_B",
        code="CO2-T+S#B",
        name="CO2 transport and storage (blue)",
        main_flow_type_out=PtxboaFlows.CO2_C,
        main_flow_type_in=PtxboaFlows.CO2_C,
        template_class_name="PtxboaProcess",
    )
    DAC = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DAC",
        code="DAC",
        name="Direct Air Capture",
        main_flow_type_out=PtxboaFlows.CO2_G,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    DAC_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DAC_B",
        code="DAC#B",
        name="Direct Air Capture (blue)",
        main_flow_type_out=PtxboaFlows.CO2_G,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    DESAL = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DESAL",
        code="DESAL",
        name="Sea Water desalination",
        main_flow_type_out=PtxboaFlows.H2O_L,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    DRI = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DRI",
        code="DRI",
        name="Green iron reduction",
        main_flow_type_out=PtxboaFlows.DRI_S,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    DRI_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DRI_B",
        code="DRI#B",
        name="Green iron reduction (blue)",
        main_flow_type_out=PtxboaFlows.B_DRI_S,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    DRI_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DRI_SB",
        code="DRI-SB",
        name="Green iron ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.DRI_S,
        main_flow_type_in=PtxboaFlows.DRI_S,
        template_class_name="PtxboaProcess",
    )
    DRI_SB_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_DRI_SB_B",
        code="DRI-SB#B",
        name="Green iron ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.B_DRI_S,
        main_flow_type_in=PtxboaFlows.B_DRI_S,
        template_class_name="PtxboaProcess",
    )
    EAF_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_EAF_B",
        code="EAF#B",
        name="electric arc furnance (blue)",
        main_flow_type_out=PtxboaFlows.STL_S,
        main_flow_type_in=PtxboaFlows.B_DRI_S,
        template_class_name="PtxboaProcess",
    )
    EFUELSYN = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_EFUELSYN",
        code="EFUELSYN",
        name="FT e-fuels Synthesis (Fischer-Tropsch)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    EFUELSYN_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_EFUELSYN_B",
        code="EFUELSYN#B",
        name="FT e-fuels Synthesis (Fischer-Tropsch) (blue)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    EFUELSYNC_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_EFUELSYNC_B",
        code="EFUELSYNC#B",
        name="FT Synthesis (Fischer-Tropsch) using NG with CCS (blue)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    EL_STR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_EL_STR",
        code="EL-STR",
        name="electricity storage",
        main_flow_type_out=PtxboaFlows.EL,
        main_flow_type_in=PtxboaFlows.EL,
        template_class_name="PtxboaProcess",
    )
    H2_COMP = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_COMP",
        code="H2-COMP",
        name="Hydrogen compression",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_COMP_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_COMP_B",
        code="H2-COMP#B",
        name="Hydrogen compression (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_LIQ = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_LIQ",
        code="H2-LIQ",
        name="Hydrogen Liquefaction",
        main_flow_type_out=PtxboaFlows.H2_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_LIQ_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_LIQ_B",
        code="H2-LIQ#B",
        name="Hydrogen Liquefaction (blue)",
        main_flow_type_out=PtxboaFlows.H2_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_L = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_L",
        code="H2-P-L",
        name="Hydrogen land pipeline new",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_L_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_L_B",
        code="H2-P-L#B",
        name="Hydrogen land pipeline new (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_LR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_LR",
        code="H2-P-LR",
        name="Hydrogen land pipeline retrofitted",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_LR_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_LR_B",
        code="H2-P-LR#B",
        name="Hydrogen land pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_S",
        code="H2-P-S",
        name="Hydrogen sea pipeline",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_S_B",
        code="H2-P-S#B",
        name="Hydrogen sea pipeline (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_SR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_SR",
        code="H2-P-SR",
        name="Hydrogen sea pipeline retrofitted",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_P_SR_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_P_SR_B",
        code="H2-P-SR#B",
        name="Hydrogen sea pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    H2_RGAS = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_RGAS",
        code="H2-RGAS",
        name="Hydrogen Regasification",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_L,
        template_class_name="PtxboaProcess",
    )
    H2_RGAS_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_RGAS_B",
        code="H2-RGAS#B",
        name="Hydrogen Regasification (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_L,
        template_class_name="PtxboaProcess",
    )
    H2_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_S",
        code="H2-S",
        name="Hydrogen ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlows.H2_L,
        main_flow_type_in=PtxboaFlows.H2_L,
        template_class_name="PtxboaProcess",
    )
    H2_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_S_B",
        code="H2-S#B",
        name="Hydrogen ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.H2_L,
        main_flow_type_in=PtxboaFlows.H2_L,
        template_class_name="PtxboaProcess",
    )
    H2_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_SB",
        code="H2-SB",
        name="Hydrogen ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.H2_L,
        main_flow_type_in=PtxboaFlows.H2_L,
        template_class_name="PtxboaProcess",
    )
    H2_SB_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_SB_B",
        code="H2-SB#B",
        name="Hydrogen ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.H2_L,
        main_flow_type_in=PtxboaFlows.H2_L,
        template_class_name="PtxboaProcess",
    )
    H2_STR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_H2_STR",
        code="H2-STR",
        name="Hydrogen storage",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    HEATPUMP_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_HEATPUMP_B",
        code="HEATPUMP#B",
        name="Large scale Heatpump (blue)",
        main_flow_type_out=PtxboaFlows.HEAT,
        main_flow_type_in=PtxboaFlows.EL,
        template_class_name="PtxboaProcess",
    )
    LOHC_CON = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_LOHC_CON",
        code="LOHC-CON",
        name="LOHC conversion",
        main_flow_type_out=PtxboaFlows.LOHC_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    LOHC_REC = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_LOHC_REC",
        code="LOHC-REC",
        name="LOHC reconversion",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.LOHC_L,
        template_class_name="PtxboaProcess",
    )
    LOHC_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_LOHC_S",
        code="LOHC-S",
        name="LOHC ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlows.LOHC_L,
        main_flow_type_in=PtxboaFlows.LOHC_L,
        template_class_name="PtxboaProcess",
    )
    LOHC_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_LOHC_SB",
        code="LOHC-SB",
        name="LOHC ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.LOHC_L,
        main_flow_type_in=PtxboaFlows.LOHC_L,
        template_class_name="PtxboaProcess",
    )
    NG_DRI_C_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NG_DRI_C_B",
        code="NG-DRI-C#B",
        name="NG-based iron reduction with CCS (blue)",
        main_flow_type_out=PtxboaFlows.B_DRI_S,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    NG_PROD_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NG_PROD_B",
        code="NG-PROD#B",
        name="production of natural gas (blue)",
        main_flow_type_out=PtxboaFlows.NG_G,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    NH3_REC = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3_REC",
        code="NH3-REC",
        name="Ammonia reconversion",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.NH3_L,
        template_class_name="PtxboaProcess",
    )
    NH3_REC_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3_REC_B",
        code="NH3-REC#B",
        name="Ammonia reconversion (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.NH3_L,
        template_class_name="PtxboaProcess",
    )
    NH3_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3_S",
        code="NH3-S",
        name="Ammonia ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlows.NH3_L,
        main_flow_type_in=PtxboaFlows.NH3_L,
        template_class_name="PtxboaProcess",
    )
    NH3_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3_S_B",
        code="NH3-S#B",
        name="Ammonia ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.NH3_L,
        main_flow_type_in=PtxboaFlows.NH3_L,
        template_class_name="PtxboaProcess",
    )
    NH3_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3_SB",
        code="NH3-SB",
        name="Ammonia ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.NH3_L,
        main_flow_type_in=PtxboaFlows.NH3_L,
        template_class_name="PtxboaProcess",
    )
    NH3_SB_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3_SB_B",
        code="NH3-SB#B",
        name="Ammonia ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.NH3_L,
        main_flow_type_in=PtxboaFlows.NH3_L,
        template_class_name="PtxboaProcess",
    )
    NH3SYN = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3SYN",
        code="NH3SYN",
        name="Ammonia Synthesis (Haber-Bosch)",
        main_flow_type_out=PtxboaFlows.NH3_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    NH3SYN_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_NH3SYN_B",
        code="NH3SYN#B",
        name="Ammonia Synthesis (Haber-Bosch) (blue)",
        main_flow_type_out=PtxboaFlows.NH3_L,
        main_flow_type_in=PtxboaFlows.H2_G,
        template_class_name="PtxboaProcess",
    )
    PEM_EL = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_PEM_EL",
        code="PEM-EL",
        name="PEM electrolysis",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.EL,
        template_class_name="PtxboaProcess",
    )
    PV_FIX = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_PV_FIX",
        code="PV-FIX",
        name="PV tilted",
        main_flow_type_out=PtxboaFlows.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    REGASATR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_REGASATR",
        code="REGASATR",
        name="Methane reconversion incl. regasification",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.CH4_L,
        template_class_name="PtxboaProcess",
    )
    RES_HYBR = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_RES_HYBR",
        code="RES-HYBR",
        name="Wind-PV-Hybrid",
        main_flow_type_out=PtxboaFlows.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    SMR_52_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SMR_52_B",
        code="SMR_52%#B",
        name="steam methane reformer with 52% carbon capture (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    SMR_52_BF_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SMR_52_BF_B",
        code="SMR_52%_BF#B",
        name="existing steam methane reformer with retrofit 52% carbon capture (blue)",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.NG_G,
        template_class_name="PtxboaProcess",
    )
    SOEC_EL = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SOEC_EL",
        code="SOEC-EL",
        name="SOEC (high-temp) electrolysis",
        main_flow_type_out=PtxboaFlows.H2_G,
        main_flow_type_in=PtxboaFlows.EL,
        template_class_name="PtxboaProcess",
    )
    SYN_S = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SYN_S",
        code="SYN-S",
        name="FT e-fuels ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.CHX_L,
        template_class_name="PtxboaProcess",
    )
    SYN_S_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SYN_S_B",
        code="SYN-S#B",
        name="FT e-fuels ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.CHX_L,
        template_class_name="PtxboaProcess",
    )
    SYN_SB = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SYN_SB",
        code="SYN-SB",
        name="FT e-fuels ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.CHX_L,
        template_class_name="PtxboaProcess",
    )
    SYN_SB_B = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_SYN_SB_B",
        code="SYN-SB#B",
        name="FT e-fuels ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlows.CHX_L,
        main_flow_type_in=PtxboaFlows.CHX_L,
        template_class_name="PtxboaProcess",
    )
    WIND_OFF = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_WIND_OFF",
        code="WIND-OFF",
        name="Wind Offshore",
        main_flow_type_out=PtxboaFlows.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
    WIND_ON = ptxboa.classes.base.PtxboaProcess._create_subclass(
        "PtxboaProcess_WIND_ON",
        code="WIND-ON",
        name="Wind Onshore",
        main_flow_type_out=PtxboaFlows.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNull,
        template_class_name="PtxboaProcess",
    )
