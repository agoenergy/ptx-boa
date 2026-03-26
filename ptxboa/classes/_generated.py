"""DO NOT EDIT (created by classes/_update.py)."""

import ptxboa.classes.base


class PtxboaParameterTypes:
    CALOR = ptxboa.classes.base.PtxboaParameterType(
        code="CALOR", name="calorific values"
    )
    CAPEX = ptxboa.classes.base.PtxboaParameterType(code="CAPEX", name="CAPEX")
    CAP_T = ptxboa.classes.base.PtxboaParameterType(
        code="CAP-T", name="transport capacity"
    )
    CBOUND = ptxboa.classes.base.PtxboaParameterType(
        code="CBOUND", name="C bound in product"
    )
    CH4SHARE = ptxboa.classes.base.PtxboaParameterType(
        code="CH4SHARE", name="methane share"
    )
    CO2CPT_R = ptxboa.classes.base.PtxboaParameterType(
        code="CO2CPT-R", name="capture rate by flow"
    )
    CO2CPT_S = ptxboa.classes.base.PtxboaParameterType(
        code="CO2CPT-S", name="CO2 for capture share"
    )
    CONV = ptxboa.classes.base.PtxboaParameterType(
        code="CONV", name="conversion factors"
    )
    CONV_OT = ptxboa.classes.base.PtxboaParameterType(
        code="CONV-OT", name="conversion factors (other fuel, transport)"
    )
    DST_S_D = ptxboa.classes.base.PtxboaParameterType(
        code="DST-S-D", name="shipping distance"
    )
    DST_S_DP = ptxboa.classes.base.PtxboaParameterType(
        code="DST-S-DP", name="pipeline distance"
    )
    EF_E = ptxboa.classes.base.PtxboaParameterType(
        code="EF_E", name="emission factor for emission balance"
    )
    EF_M = ptxboa.classes.base.PtxboaParameterType(
        code="EF_M", name="emission factor for mass balance"
    )
    EFF = ptxboa.classes.base.PtxboaParameterType(code="EFF", name="efficiency")
    FLH = ptxboa.classes.base.PtxboaParameterType(code="FLH", name="full load hours")
    LIFETIME = ptxboa.classes.base.PtxboaParameterType(
        code="LIFETIME", name="lifetime / amortization period"
    )
    LOSS = ptxboa.classes.base.PtxboaParameterType(
        code="LOSS", name="losses (own fuel)"
    )
    LOSS_T = ptxboa.classes.base.PtxboaParameterType(
        code="LOSS-T", name="losses (own fuel, transport)"
    )
    OPEX_F = ptxboa.classes.base.PtxboaParameterType(code="OPEX-F", name="OPEX (fix)")
    OPEX_O = ptxboa.classes.base.PtxboaParameterType(
        code="OPEX-O", name="OPEX (other variable)"
    )
    OPEX_T = ptxboa.classes.base.PtxboaParameterType(
        code="OPEX-T", name="levelized costs"
    )
    SEASHARE = ptxboa.classes.base.PtxboaParameterType(
        code="SEASHARE", name="sea share of pipeline distance"
    )
    SPECCOST = ptxboa.classes.base.PtxboaParameterType(
        code="SPECCOST", name="specific costs"
    )
    WACC = ptxboa.classes.base.PtxboaParameterType(code="WACC", name="WACC")


class PtxboaFlowTypes:
    B_DRI_S = ptxboa.classes.base.PtxboaFlowType(code="B-DRI-S", name="Blue iron")
    BFUEL_L = ptxboa.classes.base.PtxboaFlowType(code="BFUEL-L", name="bunker fuel")
    CH3OH_L = ptxboa.classes.base.PtxboaFlowType(
        code="CH3OH-L", name="methanol (liquid)"
    )
    CH4_G = ptxboa.classes.base.PtxboaFlowType(code="CH4-G", name="methane (gas)")
    CH4_L = ptxboa.classes.base.PtxboaFlowType(code="CH4-L", name="methane (liquid)")
    CHX_L = ptxboa.classes.base.PtxboaFlowType(code="CHX-L", name="FT e-fuels")
    CO2_C = ptxboa.classes.base.PtxboaFlowType(
        code="CO2-C", name="carbon dioxide (critical phase)"
    )
    CO2_G = ptxboa.classes.base.PtxboaFlowType(code="CO2-G", name="carbon dioxide")
    DIESEL_L = ptxboa.classes.base.PtxboaFlowType(
        code="DIESEL-L", name="diesel (liquid)"
    )
    DRI_S = ptxboa.classes.base.PtxboaFlowType(code="DRI-S", name="Green iron")
    EL = ptxboa.classes.base.PtxboaFlowType(code="EL", name="electricity")
    H2_G = ptxboa.classes.base.PtxboaFlowType(code="H2-G", name="hydrogen (gas)")
    H2_L = ptxboa.classes.base.PtxboaFlowType(code="H2-L", name="hydrogen (liquid)")
    H2O_L = ptxboa.classes.base.PtxboaFlowType(code="H2O-L", name="water")
    HEAT = ptxboa.classes.base.PtxboaFlowType(code="HEAT", name="heat")
    IOP_S = ptxboa.classes.base.PtxboaFlowType(code="IOP-S", name="iron ore pellets")
    LOHC_L = ptxboa.classes.base.PtxboaFlowType(code="LOHC-L", name="hydrogen (LOHC)")
    N2_G = ptxboa.classes.base.PtxboaFlowType(code="N2-G", name="nitrogen")
    NG_G = ptxboa.classes.base.PtxboaFlowType(code="NG-G", name="natural gas (gasous)")
    NG_L = ptxboa.classes.base.PtxboaFlowType(code="NG-L", name="natural gas (liquid)")
    NH3_L = ptxboa.classes.base.PtxboaFlowType(code="NH3-L", name="ammonia (liquid)")
    STL_S = ptxboa.classes.base.PtxboaFlowType(code="STL-S", name="crude steel")


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


class PtxboaProcessTypes:
    AEL_EL = ptxboa.classes.base.PtxboaProcessType(
        code="AEL-EL",
        name="AEL electrolysis",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    ATR = ptxboa.classes.base.PtxboaProcessType(
        code="ATR",
        name="Methane reconversion",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    ATR_91_B = ptxboa.classes.base.PtxboaProcessType(
        code="ATR_91%#B",
        name="autothermal reformer with 91% carbon capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CCGT_CC_B = ptxboa.classes.base.PtxboaSecondaryProcessType(
        code="CCGT-CC#B",
        name="Combined Cycle Gas Turbine with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH3OH_S = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OH-S",
        name="Methanol ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
    )
    CH3OH_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OH-S#B",
        name="Methanol ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
    )
    CH3OH_SB = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OH-SB",
        name="Methanol ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
    )
    CH3OH_SB_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OH-SB#B",
        name="Methanol ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
    )
    CH3OHSYC_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OHSYC#B",
        name="Methanol Synthesis classic route with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH3OHSYN = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OHSYN",
        name="Methanol Synthesis",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    CH3OHSYN_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH3OHSYN#B",
        name="Methanol Synthesis (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    CH4_COMP = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-COMP",
        name="Methane compression",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_COMP_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-COMP#B",
        name="Methane compression (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_LIQ = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-LIQ",
        name="Methane Liquefaction",
        main_flow_type_out=PtxboaFlowTypes.CH4_L,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_LIQ_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-LIQ#B",
        name="Methane Liquefaction (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_L,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_P_L = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-L",
        name="Methane land pipeline new",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_L_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-L#B",
        name="Methane land pipeline new (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_P_LR = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-LR",
        name="Methane land pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_LR_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-LR#B",
        name="Methane land pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_P_S = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-S",
        name="Methane sea pipeline",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-S#B",
        name="Methane sea pipeline (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_P_SR = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-SR",
        name="Methane sea pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_SR_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-P-SR#B",
        name="Methane sea pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_RGAS = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-RGAS",
        name="Methane Regasification",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
    )
    CH4_RGAS_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-RGAS#B",
        name="Methane Regasification (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_L,
    )
    CH4_S = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-S",
        name="LNG ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH4_L,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
    )
    CH4_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-S#B",
        name="LNG ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_L,
        main_flow_type_in=PtxboaFlowTypes.NG_L,
    )
    CH4_SB = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-SB",
        name="LNG ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH4_L,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
    )
    CH4_SB_B = ptxboa.classes.base.PtxboaProcessType(
        code="CH4-SB#B",
        name="LNG ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_L,
        main_flow_type_in=PtxboaFlowTypes.NG_L,
    )
    CH4SYN = ptxboa.classes.base.PtxboaProcessType(
        code="CH4SYN",
        name="Methane Synthesis",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    CO2_T_S_B = ptxboa.classes.base.PtxboaSecondaryProcessType(
        code="CO2-T+S#B",
        name="CO2 transport and storage (blue)",
        main_flow_type_out=PtxboaFlowTypes.CO2_C,
        main_flow_type_in=PtxboaFlowTypes.CO2_C,
    )
    DAC = ptxboa.classes.base.PtxboaSecondaryProcessType(
        code="DAC",
        name="Direct Air Capture",
        main_flow_type_out=PtxboaFlowTypes.CO2_G,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    DAC_B = ptxboa.classes.base.PtxboaSecondaryProcessType(
        code="DAC#B",
        name="Direct Air Capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.CO2_G,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    DESAL = ptxboa.classes.base.PtxboaSecondaryProcessType(
        code="DESAL",
        name="Sea Water desalination",
        main_flow_type_out=PtxboaFlowTypes.H2O_L,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    DRI = ptxboa.classes.base.PtxboaProcessType(
        code="DRI",
        name="Green iron reduction",
        main_flow_type_out=PtxboaFlowTypes.DRI_S,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    DRI_B = ptxboa.classes.base.PtxboaProcessType(
        code="DRI#B",
        name="Green iron reduction (blue)",
        main_flow_type_out=PtxboaFlowTypes.B_DRI_S,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    DRI_SB = ptxboa.classes.base.PtxboaProcessType(
        code="DRI-SB",
        name="Green iron ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.DRI_S,
        main_flow_type_in=PtxboaFlowTypes.DRI_S,
    )
    DRI_SB_B = ptxboa.classes.base.PtxboaProcessType(
        code="DRI-SB#B",
        name="Green iron ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.B_DRI_S,
        main_flow_type_in=PtxboaFlowTypes.B_DRI_S,
    )
    EAF_B = ptxboa.classes.base.PtxboaProcessType(
        code="EAF#B",
        name="electric arc furnance (blue)",
        main_flow_type_out=PtxboaFlowTypes.STL_S,
        main_flow_type_in=PtxboaFlowTypes.B_DRI_S,
    )
    EFUELSYN = ptxboa.classes.base.PtxboaProcessType(
        code="EFUELSYN",
        name="FT e-fuels Synthesis (Fischer-Tropsch)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    EFUELSYN_B = ptxboa.classes.base.PtxboaProcessType(
        code="EFUELSYN#B",
        name="FT e-fuels Synthesis (Fischer-Tropsch) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    EFUELSYNC_B = ptxboa.classes.base.PtxboaProcessType(
        code="EFUELSYNC#B",
        name="FT Synthesis (Fischer-Tropsch) using NG with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    EL_STR = ptxboa.classes.base.PtxboaProcessType(
        code="EL-STR",
        name="electricity storage",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    H2_COMP = ptxboa.classes.base.PtxboaProcessType(
        code="H2-COMP",
        name="Hydrogen compression",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_COMP_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-COMP#B",
        name="Hydrogen compression (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_LIQ = ptxboa.classes.base.PtxboaProcessType(
        code="H2-LIQ",
        name="Hydrogen Liquefaction",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_LIQ_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-LIQ#B",
        name="Hydrogen Liquefaction (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_L = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-L",
        name="Hydrogen land pipeline new",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_L_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-L#B",
        name="Hydrogen land pipeline new (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_LR = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-LR",
        name="Hydrogen land pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_LR_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-LR#B",
        name="Hydrogen land pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_S = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-S",
        name="Hydrogen sea pipeline",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-S#B",
        name="Hydrogen sea pipeline (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_SR = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-SR",
        name="Hydrogen sea pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_SR_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-P-SR#B",
        name="Hydrogen sea pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_RGAS = ptxboa.classes.base.PtxboaProcessType(
        code="H2-RGAS",
        name="Hydrogen Regasification",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_RGAS_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-RGAS#B",
        name="Hydrogen Regasification (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_S = ptxboa.classes.base.PtxboaProcessType(
        code="H2-S",
        name="Hydrogen ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-S#B",
        name="Hydrogen ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_SB = ptxboa.classes.base.PtxboaProcessType(
        code="H2-SB",
        name="Hydrogen ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_SB_B = ptxboa.classes.base.PtxboaProcessType(
        code="H2-SB#B",
        name="Hydrogen ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_STR = ptxboa.classes.base.PtxboaProcessType(
        code="H2-STR",
        name="Hydrogen storage",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    HEATPUMP_B = ptxboa.classes.base.PtxboaSecondaryProcessType(
        code="HEATPUMP#B",
        name="Large scale Heatpump (blue)",
        main_flow_type_out=PtxboaFlowTypes.HEAT,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    LOHC_CON = ptxboa.classes.base.PtxboaProcessType(
        code="LOHC-CON",
        name="LOHC conversion",
        main_flow_type_out=PtxboaFlowTypes.LOHC_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    LOHC_REC = ptxboa.classes.base.PtxboaProcessType(
        code="LOHC-REC",
        name="LOHC reconversion",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.LOHC_L,
    )
    LOHC_S = ptxboa.classes.base.PtxboaProcessType(
        code="LOHC-S",
        name="LOHC ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.LOHC_L,
        main_flow_type_in=PtxboaFlowTypes.LOHC_L,
    )
    LOHC_SB = ptxboa.classes.base.PtxboaProcessType(
        code="LOHC-SB",
        name="LOHC ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.LOHC_L,
        main_flow_type_in=PtxboaFlowTypes.LOHC_L,
    )
    NG_DRI_C_B = ptxboa.classes.base.PtxboaProcessType(
        code="NG-DRI-C#B",
        name="NG-based iron reduction with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.B_DRI_S,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    NG_PROD_B = ptxboa.classes.base.PtxboaProcessType(
        code="NG-PROD#B",
        name="production of natural gas (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    NH3_REC = ptxboa.classes.base.PtxboaProcessType(
        code="NH3-REC",
        name="Ammonia reconversion",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3_REC_B = ptxboa.classes.base.PtxboaProcessType(
        code="NH3-REC#B",
        name="Ammonia reconversion (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3_S = ptxboa.classes.base.PtxboaProcessType(
        code="NH3-S",
        name="Ammonia ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="NH3-S#B",
        name="Ammonia ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3_SB = ptxboa.classes.base.PtxboaProcessType(
        code="NH3-SB",
        name="Ammonia ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3_SB_B = ptxboa.classes.base.PtxboaProcessType(
        code="NH3-SB#B",
        name="Ammonia ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3SYN = ptxboa.classes.base.PtxboaProcessType(
        code="NH3SYN",
        name="Ammonia Synthesis (Haber-Bosch)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    NH3SYN_B = ptxboa.classes.base.PtxboaProcessType(
        code="NH3SYN#B",
        name="Ammonia Synthesis (Haber-Bosch) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    PEM_EL = ptxboa.classes.base.PtxboaProcessType(
        code="PEM-EL",
        name="PEM electrolysis",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    PV_FIX = ptxboa.classes.base.PtxboaProcessType(
        code="PV-FIX",
        name="PV tilted",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    REGASATR = ptxboa.classes.base.PtxboaProcessType(
        code="REGASATR",
        name="Methane reconversion incl. regasification",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
    )
    RES_HYBR = ptxboa.classes.base.PtxboaProcessType(
        code="RES-HYBR",
        name="Wind-PV-Hybrid",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    SMR_52_B = ptxboa.classes.base.PtxboaProcessType(
        code="SMR_52%#B",
        name="steam methane reformer with 52% carbon capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    SMR_52_BF_B = ptxboa.classes.base.PtxboaProcessType(
        code="SMR_52%_BF#B",
        name="existing steam methane reformer with retrofit 52% carbon capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    SOEC_EL = ptxboa.classes.base.PtxboaProcessType(
        code="SOEC-EL",
        name="SOEC (high-temp) electrolysis",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    SYN_S = ptxboa.classes.base.PtxboaProcessType(
        code="SYN-S",
        name="FT e-fuels ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
    )
    SYN_S_B = ptxboa.classes.base.PtxboaProcessType(
        code="SYN-S#B",
        name="FT e-fuels ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
    )
    SYN_SB = ptxboa.classes.base.PtxboaProcessType(
        code="SYN-SB",
        name="FT e-fuels ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
    )
    SYN_SB_B = ptxboa.classes.base.PtxboaProcessType(
        code="SYN-SB#B",
        name="FT e-fuels ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
    )
    WIND_OFF = ptxboa.classes.base.PtxboaProcessType(
        code="WIND-OFF",
        name="Wind Offshore",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
    WIND_ON = ptxboa.classes.base.PtxboaProcessType(
        code="WIND-ON",
        name="Wind Onshore",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=ptxboa.classes.base.PtxboaFlowNullType,
    )
