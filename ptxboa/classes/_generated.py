"""DO NOT EDIT (created by classes/_update.py)."""

from ptxboa.classes.base import (
    PtxboaEnum,
    PtxboaFlowNullType,
    PtxboaFlowType,
    PtxboaParameterType,
    PtxboaRegion,
)
from ptxboa.classes.extra import (
    PtxboaChainBlueTemplate,
    PtxboaChainGreenTemplate,
    PtxboaChainTemplate,
    PtxboaProcessType,
    PtxboaSecondaryProcessType,
    PtxboaTransportProcessType,
)


class PtxboaParameterTypes(PtxboaEnum):
    CALOR = PtxboaParameterType(code="CALOR", name="calorific values")
    CAPEX = PtxboaParameterType(code="CAPEX", name="CAPEX")
    CAP_T = PtxboaParameterType(code="CAP-T", name="transport capacity")
    CBOUND = PtxboaParameterType(code="CBOUND", name="C bound in product")
    CH4SHARE = PtxboaParameterType(code="CH4SHARE", name="methane share")
    CO2CPT_R = PtxboaParameterType(code="CO2CPT-R", name="capture rate by flow")
    CO2CPT_S = PtxboaParameterType(code="CO2CPT-S", name="CO2 for capture share")
    CONV = PtxboaParameterType(code="CONV", name="conversion factors")
    CONV_OT = PtxboaParameterType(
        code="CONV-OT", name="conversion factors (other fuel, transport)"
    )
    DST_S_D = PtxboaParameterType(code="DST-S-D", name="shipping distance")
    DST_S_DP = PtxboaParameterType(code="DST-S-DP", name="pipeline distance")
    EF_E = PtxboaParameterType(code="EF_E", name="emission factor for emission balance")
    EF_M = PtxboaParameterType(code="EF_M", name="emission factor for mass balance")
    EFF = PtxboaParameterType(code="EFF", name="efficiency")
    FLH = PtxboaParameterType(code="FLH", name="full load hours")
    LIFETIME = PtxboaParameterType(
        code="LIFETIME", name="lifetime / amortization period"
    )
    LOSS = PtxboaParameterType(code="LOSS", name="losses (own fuel)")
    LOSS_T = PtxboaParameterType(code="LOSS-T", name="losses (own fuel, transport)")
    OPEX_F = PtxboaParameterType(code="OPEX-F", name="OPEX (fix)")
    OPEX_O = PtxboaParameterType(code="OPEX-O", name="OPEX (other variable)")
    OPEX_T = PtxboaParameterType(code="OPEX-T", name="levelized costs")
    SEASHARE = PtxboaParameterType(
        code="SEASHARE", name="sea share of pipeline distance"
    )
    SPECCOST = PtxboaParameterType(code="SPECCOST", name="specific costs")
    WACC = PtxboaParameterType(code="WACC", name="WACC")


class PtxboaFlowTypes(PtxboaEnum):
    B_DRI_S = PtxboaFlowType(code="B-DRI-S", name="Blue iron")
    BFUEL_L = PtxboaFlowType(code="BFUEL-L", name="bunker fuel")
    CH3OH_L = PtxboaFlowType(code="CH3OH-L", name="methanol (liquid)")
    CH4_G = PtxboaFlowType(code="CH4-G", name="methane (gas)")
    CH4_L = PtxboaFlowType(code="CH4-L", name="methane (liquid)")
    CHX_L = PtxboaFlowType(code="CHX-L", name="FT e-fuels")
    CO2_C = PtxboaFlowType(code="CO2-C", name="carbon dioxide (critical phase)")
    CO2_G = PtxboaFlowType(code="CO2-G", name="carbon dioxide")
    DIESEL_L = PtxboaFlowType(code="DIESEL-L", name="diesel (liquid)")
    DRI_S = PtxboaFlowType(code="DRI-S", name="Green iron")
    EL = PtxboaFlowType(code="EL", name="electricity")
    H2_G = PtxboaFlowType(code="H2-G", name="hydrogen (gas)")
    H2_L = PtxboaFlowType(code="H2-L", name="hydrogen (liquid)")
    H2O_L = PtxboaFlowType(code="H2O-L", name="water")
    HEAT = PtxboaFlowType(code="HEAT", name="heat")
    IOP_S = PtxboaFlowType(code="IOP-S", name="iron ore pellets")
    LOHC_L = PtxboaFlowType(code="LOHC-L", name="hydrogen (LOHC)")
    N2_G = PtxboaFlowType(code="N2-G", name="nitrogen")
    NG_G = PtxboaFlowType(code="NG-G", name="natural gas (gasous)")
    NG_L = PtxboaFlowType(code="NG-L", name="natural gas (liquid)")
    NH3_L = PtxboaFlowType(code="NH3-L", name="ammonia (liquid)")
    STL_S = PtxboaFlowType(code="STL-S", name="crude steel")


class PtxboaRegions(PtxboaEnum):
    ARE = PtxboaRegion(code="ARE", name="United Arab Emirates")
    ARG = PtxboaRegion(code="ARG", name="Argentina")
    ARG_BA = PtxboaRegion(code="ARG-BA", name="Argentina (Buenos Aires)")
    ARG_CAT = PtxboaRegion(code="ARG-CAT", name="Argentina (Catamarca)")
    ARG_CBA = PtxboaRegion(
        code="ARG-CBA", name="Argentina (Autonomous City of Buenos Aires)"
    )
    ARG_CHA = PtxboaRegion(code="ARG-CHA", name="Argentina (Chaco)")
    ARG_CHU = PtxboaRegion(code="ARG-CHU", name="Argentina (Chubut)")
    ARG_COR = PtxboaRegion(code="ARG-COR", name="Argentina (Corrientes)")
    ARG_CRB = PtxboaRegion(code="ARG-CRB", name="Argentina (Córdoba)")
    ARG_CRU = PtxboaRegion(code="ARG-CRU", name="Argentina (Santa Cruz)")
    ARG_EST = PtxboaRegion(code="ARG-EST", name="Argentina (Santiago del Estero)")
    ARG_FOR = PtxboaRegion(code="ARG-FOR", name="Argentina (Formosa)")
    ARG_FUE = PtxboaRegion(
        code="ARG-FUE",
        name="Argentina (Tierra del Fuego, Antártida e Islas del Atlántico Sur)",
    )
    ARG_JUJ = PtxboaRegion(code="ARG-JUJ", name="Argentina (Jujuy)")
    ARG_LAR = PtxboaRegion(code="ARG-LAR", name="Argentina (La Rioja)")
    ARG_MEN = PtxboaRegion(code="ARG-MEN", name="Argentina (Mendoza)")
    ARG_MIS = PtxboaRegion(code="ARG-MIS", name="Argentina (Misiones)")
    ARG_NEG = PtxboaRegion(code="ARG-NEG", name="Argentina (Río Negro)")
    ARG_NEU = PtxboaRegion(code="ARG-NEU", name="Argentina (Neuquén)")
    ARG_PAM = PtxboaRegion(code="ARG-PAM", name="Argentina (La Pampa)")
    ARG_RIO = PtxboaRegion(code="ARG-RIO", name="Argentina (Entre Ríos)")
    ARG_SAF = PtxboaRegion(code="ARG-SAF", name="Argentina (Santa Fe)")
    ARG_SAJ = PtxboaRegion(code="ARG-SAJ", name="Argentina (San Juan)")
    ARG_SAL = PtxboaRegion(code="ARG-SAL", name="Argentina (San Luis)")
    ARG_SAT = PtxboaRegion(code="ARG-SAT", name="Argentina (Salta)")
    ARG_TUC = PtxboaRegion(code="ARG-TUC", name="Argentina (Tucumán)")
    AUS = PtxboaRegion(code="AUS", name="Australia")
    BRA = PtxboaRegion(code="BRA", name="Brazil")
    CHL = PtxboaRegion(code="CHL", name="Chile")
    CHN = PtxboaRegion(code="CHN", name="China")
    COL = PtxboaRegion(code="COL", name="Colombia")
    CRI = PtxboaRegion(code="CRI", name="Costa Rica")
    DEU = PtxboaRegion(code="DEU", name="Germany")
    DNK = PtxboaRegion(code="DNK", name="Denmark")
    DZA = PtxboaRegion(code="DZA", name="Algeria")
    EGY = PtxboaRegion(code="EGY", name="Egypt")
    ESP = PtxboaRegion(code="ESP", name="Spain")
    FRA = PtxboaRegion(code="FRA", name="France")
    IDN = PtxboaRegion(code="IDN", name="Indonesia")
    IND = PtxboaRegion(code="IND", name="India")
    JOR = PtxboaRegion(code="JOR", name="Jordan")
    JPN = PtxboaRegion(code="JPN", name="Japan")
    KAZ = PtxboaRegion(code="KAZ", name="Kazakhstan")
    KEN = PtxboaRegion(code="KEN", name="Kenya")
    KOR = PtxboaRegion(code="KOR", name="South Korea")
    MAR = PtxboaRegion(code="MAR", name="Morocco")
    MAR_BEN = PtxboaRegion(code="MAR-BEN", name="Morocco (Béni Mellal-Khénifra)")
    MAR_CAS = PtxboaRegion(code="MAR-CAS", name="Morocco (Casablanca)")
    MAR_DAK = PtxboaRegion(code="MAR-DAK", name="Morocco (Dakhla-Oued Ed-Dahab)")
    MAR_DRA = PtxboaRegion(code="MAR-DRA", name="Morocco (Drâa-Tafilalet)")
    MAR_FES = PtxboaRegion(code="MAR-FES", name="Morocco (Fès-Meknès)")
    MAR_GUE = PtxboaRegion(code="MAR-GUE", name="Morocco (Guelmim-Oued Noun)")
    MAR_LAA = PtxboaRegion(code="MAR-LAA", name="Morocco (Laâyoune-Sakia El Hamra)")
    MAR_LOR = PtxboaRegion(code="MAR-LOR", name="Morocco (L´oriental)")
    MAR_MAR = PtxboaRegion(code="MAR-MAR", name="Morocco (Marrakech-Safi)")
    MAR_RAB = PtxboaRegion(code="MAR-RAB", name="Morocco (Rabat-Salé-Kénitra)")
    MAR_SOU = PtxboaRegion(code="MAR-SOU", name="Morocco (Souss-Massa)")
    MAR_TAN = PtxboaRegion(code="MAR-TAN", name="Morocco (Tangier)")
    MEX = PtxboaRegion(code="MEX", name="Mexico")
    MRT = PtxboaRegion(code="MRT", name="Mauritania")
    MYS = PtxboaRegion(code="MYS", name="Malaysia")
    NAM = PtxboaRegion(code="NAM", name="Namibia")
    NLD = PtxboaRegion(code="NLD", name="Netherlands")
    NOR = PtxboaRegion(code="NOR", name="Norway")
    OMN = PtxboaRegion(code="OMN", name="Oman")
    PER = PtxboaRegion(code="PER", name="Peru")
    PRT = PtxboaRegion(code="PRT", name="Portugal")
    QAT = PtxboaRegion(code="QAT", name="Qatar")
    RUS = PtxboaRegion(code="RUS", name="Russia")
    SAU = PtxboaRegion(code="SAU", name="Saudi Arabia")
    SWE = PtxboaRegion(code="SWE", name="Sweden")
    THA = PtxboaRegion(code="THA", name="Thailand")
    TUN = PtxboaRegion(code="TUN", name="Tunisia")
    UKR = PtxboaRegion(code="UKR", name="Ukraine")
    URY = PtxboaRegion(code="URY", name="Uruguay")
    USA = PtxboaRegion(code="USA", name="USA")
    VNM = PtxboaRegion(code="VNM", name="Vietnam")
    ZAF = PtxboaRegion(code="ZAF", name="South Africa")
    ZAF_EC = PtxboaRegion(code="ZAF-EC", name="South Africa (East Cape)")
    ZAF_FRS = PtxboaRegion(code="ZAF-FRS", name="South Africa (Free State)")
    ZAF_GAU = PtxboaRegion(code="ZAF-GAU", name="South Africa (Gauteng)")
    ZAF_KWA = PtxboaRegion(code="ZAF-KWA", name="South Africa (KwaZulu-Natal)")
    ZAF_LIM = PtxboaRegion(code="ZAF-LIM", name="South Africa (Limpopo)")
    ZAF_MPU = PtxboaRegion(code="ZAF-MPU", name="South Africa (Mpumalanga)")
    ZAF_NC = PtxboaRegion(code="ZAF-NC", name="South Africa (Northern Cape)")
    ZAF_NW = PtxboaRegion(code="ZAF-NW", name="South Africa (North West)")
    ZAF_WC = PtxboaRegion(code="ZAF-WC", name="South Africa (Western Cape)")


class PtxboaProcessTypes(PtxboaEnum):
    AEL_EL = PtxboaProcessType(
        code="AEL-EL",
        name="AEL electrolysis",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.EL,
        secondary_flow_types={PtxboaFlowTypes.H2O_L},
    )
    ATR = PtxboaProcessType(
        code="ATR",
        name="Methane reconversion",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    ATR_91_B = PtxboaProcessType(
        code="ATR_91%#B",
        name="autothermal reformer with 91% carbon capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.CO2_C, PtxboaFlowTypes.EL},
    )
    CCGT_CC_B = PtxboaSecondaryProcessType(
        code="CCGT-CC#B",
        name="Combined Cycle Gas Turbine with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.CO2_C},
    )
    CH3OH_S = PtxboaTransportProcessType(
        code="CH3OH-S",
        name="Methanol ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
    )
    CH3OH_S_B = PtxboaTransportProcessType(
        code="CH3OH-S#B",
        name="Methanol ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    CH3OH_SB = PtxboaTransportProcessType(
        code="CH3OH-SB",
        name="Methanol ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    CH3OH_SB_B = PtxboaTransportProcessType(
        code="CH3OH-SB#B",
        name="Methanol ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.CH3OH_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    CH3OHSYC_B = PtxboaProcessType(
        code="CH3OHSYC#B",
        name="Methanol Synthesis classic route with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.EL, PtxboaFlowTypes.CO2_C},
    )
    CH3OHSYN = PtxboaProcessType(
        code="CH3OHSYN",
        name="Methanol Synthesis",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL, PtxboaFlowTypes.CO2_G},
    )
    CH3OHSYN_B = PtxboaProcessType(
        code="CH3OHSYN#B",
        name="Methanol Synthesis (blue)",
        main_flow_type_out=PtxboaFlowTypes.CH3OH_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={
            PtxboaFlowTypes.CO2_G,
            PtxboaFlowTypes.HEAT,
            PtxboaFlowTypes.EL,
        },
    )
    CH4_COMP = PtxboaProcessType(
        code="CH4-COMP",
        name="Methane compression",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    CH4_COMP_B = PtxboaProcessType(
        code="CH4-COMP#B",
        name="Methane compression (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    CH4_LIQ = PtxboaProcessType(
        code="CH4-LIQ",
        name="Methane Liquefaction",
        main_flow_type_out=PtxboaFlowTypes.CH4_L,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    CH4_LIQ_B = PtxboaProcessType(
        code="CH4-LIQ#B",
        name="Methane Liquefaction (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_L,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    CH4_P_L = PtxboaTransportProcessType(
        code="CH4-P-L",
        name="Methane land pipeline new",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_L_B = PtxboaTransportProcessType(
        code="CH4-P-L#B",
        name="Methane land pipeline new (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.NG_G},
    )
    CH4_P_LR = PtxboaTransportProcessType(
        code="CH4-P-LR",
        name="Methane land pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_LR_B = PtxboaTransportProcessType(
        code="CH4-P-LR#B",
        name="Methane land pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_P_S = PtxboaTransportProcessType(
        code="CH4-P-S",
        name="Methane sea pipeline",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_S_B = PtxboaTransportProcessType(
        code="CH4-P-S#B",
        name="Methane sea pipeline (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_P_SR = PtxboaTransportProcessType(
        code="CH4-P-SR",
        name="Methane sea pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_G,
    )
    CH4_P_SR_B = PtxboaTransportProcessType(
        code="CH4-P-SR#B",
        name="Methane sea pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
    )
    CH4_RGAS = PtxboaProcessType(
        code="CH4-RGAS",
        name="Methane Regasification",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
    )
    CH4_RGAS_B = PtxboaProcessType(
        code="CH4-RGAS#B",
        name="Methane Regasification (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowTypes.NG_L,
        secondary_flow_types={
            PtxboaFlowTypes.DIESEL_L,
            PtxboaFlowTypes.EL,
            PtxboaFlowTypes.NG_G,
        },
    )
    CH4_S = PtxboaTransportProcessType(
        code="CH4-S",
        name="LNG ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH4_L,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
    )
    CH4_S_B = PtxboaTransportProcessType(
        code="CH4-S#B",
        name="LNG ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_L,
        main_flow_type_in=PtxboaFlowTypes.NG_L,
        secondary_flow_types={PtxboaFlowTypes.NG_L},
    )
    CH4_SB = PtxboaTransportProcessType(
        code="CH4-SB",
        name="LNG ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CH4_L,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    CH4_SB_B = PtxboaTransportProcessType(
        code="CH4-SB#B",
        name="LNG ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_L,
        main_flow_type_in=PtxboaFlowTypes.NG_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L, PtxboaFlowTypes.NG_L},
    )
    CH4SYN = PtxboaProcessType(
        code="CH4SYN",
        name="Methane Synthesis",
        main_flow_type_out=PtxboaFlowTypes.CH4_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={
            PtxboaFlowTypes.CO2_G,
            PtxboaFlowTypes.H2O_L,
            PtxboaFlowTypes.HEAT,
        },
    )
    CO2_T_S_B = PtxboaSecondaryProcessType(
        code="CO2-T+S#B",
        name="CO2 transport and storage (blue)",
        main_flow_type_out=PtxboaFlowTypes.CO2_C,
        main_flow_type_in=PtxboaFlowTypes.CO2_C,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    DAC = PtxboaSecondaryProcessType(
        code="DAC",
        name="Direct Air Capture",
        main_flow_type_out=PtxboaFlowTypes.CO2_G,
        main_flow_type_in=PtxboaFlowNullType,
        secondary_flow_types={
            PtxboaFlowTypes.H2O_L,
            PtxboaFlowTypes.HEAT,
            PtxboaFlowTypes.EL,
        },
    )
    DAC_B = PtxboaSecondaryProcessType(
        code="DAC#B",
        name="Direct Air Capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.CO2_G,
        main_flow_type_in=PtxboaFlowNullType,
        secondary_flow_types={PtxboaFlowTypes.HEAT, PtxboaFlowTypes.EL},
    )
    DESAL = PtxboaSecondaryProcessType(
        code="DESAL",
        name="Sea Water desalination",
        main_flow_type_out=PtxboaFlowTypes.H2O_L,
        main_flow_type_in=PtxboaFlowNullType,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    DRI = PtxboaProcessType(
        code="DRI",
        name="Green iron reduction",
        main_flow_type_out=PtxboaFlowTypes.DRI_S,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    DRI_B = PtxboaProcessType(
        code="DRI#B",
        name="Green iron reduction (blue)",
        main_flow_type_out=PtxboaFlowTypes.B_DRI_S,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.IOP_S, PtxboaFlowTypes.EL},
    )
    DRI_SB = PtxboaTransportProcessType(
        code="DRI-SB",
        name="Green iron ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.DRI_S,
        main_flow_type_in=PtxboaFlowTypes.DRI_S,
    )
    DRI_SB_B = PtxboaTransportProcessType(
        code="DRI-SB#B",
        name="Green iron ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.B_DRI_S,
        main_flow_type_in=PtxboaFlowTypes.B_DRI_S,
    )
    EAF_B = PtxboaProcessType(
        code="EAF#B",
        name="electric arc furnance (blue)",
        main_flow_type_out=PtxboaFlowTypes.STL_S,
        main_flow_type_in=PtxboaFlowTypes.B_DRI_S,
        secondary_flow_types={PtxboaFlowTypes.NG_G, PtxboaFlowTypes.EL},
    )
    EFUELSYN = PtxboaProcessType(
        code="EFUELSYN",
        name="FT e-fuels Synthesis (Fischer-Tropsch)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={
            PtxboaFlowTypes.CO2_G,
            PtxboaFlowTypes.EL,
            PtxboaFlowTypes.H2O_L,
            PtxboaFlowTypes.HEAT,
        },
    )
    EFUELSYN_B = PtxboaProcessType(
        code="EFUELSYN#B",
        name="FT e-fuels Synthesis (Fischer-Tropsch) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={
            PtxboaFlowTypes.HEAT,
            PtxboaFlowTypes.EL,
            PtxboaFlowTypes.CO2_G,
        },
    )
    EFUELSYNC_B = PtxboaProcessType(
        code="EFUELSYNC#B",
        name="FT Synthesis (Fischer-Tropsch) using NG with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.EL, PtxboaFlowTypes.CO2_C},
    )
    EL_STR = PtxboaTransportProcessType(
        code="EL-STR",
        name="electricity storage",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    H2_COMP = PtxboaProcessType(
        code="H2-COMP",
        name="Hydrogen compression",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    H2_COMP_B = PtxboaProcessType(
        code="H2-COMP#B",
        name="Hydrogen compression (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    H2_LIQ = PtxboaProcessType(
        code="H2-LIQ",
        name="Hydrogen Liquefaction",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    H2_LIQ_B = PtxboaProcessType(
        code="H2-LIQ#B",
        name="Hydrogen Liquefaction (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    H2_P_L = PtxboaTransportProcessType(
        code="H2-P-L",
        name="Hydrogen land pipeline new",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_L_B = PtxboaTransportProcessType(
        code="H2-P-L#B",
        name="Hydrogen land pipeline new (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_LR = PtxboaTransportProcessType(
        code="H2-P-LR",
        name="Hydrogen land pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_LR_B = PtxboaTransportProcessType(
        code="H2-P-LR#B",
        name="Hydrogen land pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_S = PtxboaTransportProcessType(
        code="H2-P-S",
        name="Hydrogen sea pipeline",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_S_B = PtxboaTransportProcessType(
        code="H2-P-S#B",
        name="Hydrogen sea pipeline (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_SR = PtxboaTransportProcessType(
        code="H2-P-SR",
        name="Hydrogen sea pipeline retrofitted",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_P_SR_B = PtxboaTransportProcessType(
        code="H2-P-SR#B",
        name="Hydrogen sea pipeline retrofitted (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    H2_RGAS = PtxboaProcessType(
        code="H2-RGAS",
        name="Hydrogen Regasification",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_RGAS_B = PtxboaProcessType(
        code="H2-RGAS#B",
        name="Hydrogen Regasification (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_S = PtxboaTransportProcessType(
        code="H2-S",
        name="Hydrogen ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
    )
    H2_S_B = PtxboaTransportProcessType(
        code="H2-S#B",
        name="Hydrogen ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
        secondary_flow_types={PtxboaFlowTypes.H2_L},
    )
    H2_SB = PtxboaTransportProcessType(
        code="H2-SB",
        name="Hydrogen ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    H2_SB_B = PtxboaTransportProcessType(
        code="H2-SB#B",
        name="Hydrogen ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_L,
        main_flow_type_in=PtxboaFlowTypes.H2_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    H2_STR = PtxboaTransportProcessType(
        code="H2-STR",
        name="Hydrogen storage",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
    )
    HEATPUMP_B = PtxboaSecondaryProcessType(
        code="HEATPUMP#B",
        name="Large scale Heatpump (blue)",
        main_flow_type_out=PtxboaFlowTypes.HEAT,
        main_flow_type_in=PtxboaFlowTypes.EL,
    )
    LOHC_CON = PtxboaProcessType(
        code="LOHC-CON",
        name="LOHC conversion",
        main_flow_type_out=PtxboaFlowTypes.LOHC_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    LOHC_REC = PtxboaProcessType(
        code="LOHC-REC",
        name="LOHC reconversion",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.LOHC_L,
        secondary_flow_types={PtxboaFlowTypes.HEAT, PtxboaFlowTypes.EL},
    )
    LOHC_S = PtxboaTransportProcessType(
        code="LOHC-S",
        name="LOHC ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.LOHC_L,
        main_flow_type_in=PtxboaFlowTypes.LOHC_L,
    )
    LOHC_SB = PtxboaTransportProcessType(
        code="LOHC-SB",
        name="LOHC ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.LOHC_L,
        main_flow_type_in=PtxboaFlowTypes.LOHC_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    NG_DRI_C_B = PtxboaProcessType(
        code="NG-DRI-C#B",
        name="NG-based iron reduction with CCS (blue)",
        main_flow_type_out=PtxboaFlowTypes.B_DRI_S,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={
            PtxboaFlowTypes.CO2_C,
            PtxboaFlowTypes.CH4_G,
            PtxboaFlowTypes.EL,
            PtxboaFlowTypes.IOP_S,
        },
    )
    NG_PROD_B = PtxboaProcessType(
        code="NG-PROD#B",
        name="production of natural gas (blue)",
        main_flow_type_out=PtxboaFlowTypes.NG_G,
        main_flow_type_in=PtxboaFlowNullType,
        secondary_flow_types={PtxboaFlowTypes.DIESEL_L},
    )
    NH3_REC = PtxboaProcessType(
        code="NH3-REC",
        name="Ammonia reconversion",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    NH3_REC_B = PtxboaProcessType(
        code="NH3-REC#B",
        name="Ammonia reconversion (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    NH3_S = PtxboaTransportProcessType(
        code="NH3-S",
        name="Ammonia ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
    )
    NH3_S_B = PtxboaTransportProcessType(
        code="NH3-S#B",
        name="Ammonia ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
        secondary_flow_types={PtxboaFlowTypes.NH3_L},
    )
    NH3_SB = PtxboaTransportProcessType(
        code="NH3-SB",
        name="Ammonia ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    NH3_SB_B = PtxboaTransportProcessType(
        code="NH3-SB#B",
        name="Ammonia ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.NH3_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    NH3SYN = PtxboaProcessType(
        code="NH3SYN",
        name="Ammonia Synthesis (Haber-Bosch)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.N2_G, PtxboaFlowTypes.EL},
    )
    NH3SYN_B = PtxboaProcessType(
        code="NH3SYN#B",
        name="Ammonia Synthesis (Haber-Bosch) (blue)",
        main_flow_type_out=PtxboaFlowTypes.NH3_L,
        main_flow_type_in=PtxboaFlowTypes.H2_G,
        secondary_flow_types={PtxboaFlowTypes.HEAT, PtxboaFlowTypes.EL},
    )
    PEM_EL = PtxboaProcessType(
        code="PEM-EL",
        name="PEM electrolysis",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.EL,
        secondary_flow_types={PtxboaFlowTypes.H2O_L},
    )
    PV_FIX = PtxboaProcessType(
        code="PV-FIX",
        name="PV tilted",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowNullType,
    )
    REGASATR = PtxboaProcessType(
        code="REGASATR",
        name="Methane reconversion incl. regasification",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.CH4_L,
        secondary_flow_types={PtxboaFlowTypes.EL},
    )
    RES_HYBR = PtxboaProcessType(
        code="RES-HYBR",
        name="Wind-PV-Hybrid",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowNullType,
    )
    SMR_52_B = PtxboaProcessType(
        code="SMR_52%#B",
        name="steam methane reformer with 52% carbon capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.CO2_C, PtxboaFlowTypes.EL},
    )
    SMR_52_BF_B = PtxboaProcessType(
        code="SMR_52%_BF#B",
        name="existing steam methane reformer with retrofit 52% carbon capture (blue)",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.NG_G,
        secondary_flow_types={PtxboaFlowTypes.CO2_C, PtxboaFlowTypes.EL},
    )
    SOEC_EL = PtxboaProcessType(
        code="SOEC-EL",
        name="SOEC (high-temp) electrolysis",
        main_flow_type_out=PtxboaFlowTypes.H2_G,
        main_flow_type_in=PtxboaFlowTypes.EL,
        secondary_flow_types={PtxboaFlowTypes.H2O_L},
    )
    SYN_S = PtxboaTransportProcessType(
        code="SYN-S",
        name="FT e-fuels ship (own fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
    )
    SYN_S_B = PtxboaTransportProcessType(
        code="SYN-S#B",
        name="FT e-fuels ship (own fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    SYN_SB = PtxboaTransportProcessType(
        code="SYN-SB",
        name="FT e-fuels ship (bunker fuel consumption)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    SYN_SB_B = PtxboaTransportProcessType(
        code="SYN-SB#B",
        name="FT e-fuels ship (bunker fuel consumption) (blue)",
        main_flow_type_out=PtxboaFlowTypes.CHX_L,
        main_flow_type_in=PtxboaFlowTypes.CHX_L,
        secondary_flow_types={PtxboaFlowTypes.BFUEL_L},
    )
    WIND_OFF = PtxboaProcessType(
        code="WIND-OFF",
        name="Wind Offshore",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowNullType,
    )
    WIND_ON = PtxboaProcessType(
        code="WIND-ON",
        name="Wind Onshore",
        main_flow_type_out=PtxboaFlowTypes.EL,
        main_flow_type_in=PtxboaFlowNullType,
    )


class PtxboaChainTemplates(PtxboaEnum):
    BLUE_IRON_BLUE_ = PtxboaChainTemplate(
        code="Blue Iron (blue)*",
        name="TEST Blue Iron (blue)*",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.NG_DRI_C_B,
            PtxboaProcessTypes.DRI_SB_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    CH3OH_L_ATR_91_CH3OHSYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CH3OH-L__ATR_91%_CH3OHSYN__prod_in_demand",
        name="Methanol (ATR)*",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.CH3OHSYN_B,
        ),
    )
    CH3OH_L_ATR_91_CH3OHSYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CH3OH-L__ATR_91%_CH3OHSYN__prod_in_supply",
        name="Methanol (ATR)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.CH3OHSYN_B,
            PtxboaProcessTypes.CH3OH_SB_B,
            PtxboaProcessTypes.CH3OH_S_B,
        ),
    )
    CH3OH_L_CH3OHSYC_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CH3OH-L__CH3OHSYC__prod_in_demand",
        name="Methanol (NG-based)*",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.CH3OHSYC_B,
        ),
    )
    CH3OH_L_CH3OHSYC_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CH3OH-L__CH3OHSYC__prod_in_supply",
        name="Methanol (NG-based)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.CH3OHSYC_B,
            PtxboaProcessTypes.CH3OH_SB_B,
            PtxboaProcessTypes.CH3OH_S_B,
        ),
    )
    CH3OH_L_SMR_52_BF_CH3OHSYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CH3OH-L__SMR_52%_BF_CH3OHSYN__prod_in_demand",
        name="Methanol (SMR-BF)*",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.CH3OHSYN_B,
        ),
    )
    CH3OH_L_SMR_52_BF_CH3OHSYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CH3OH-L__SMR_52%_BF_CH3OHSYN__prod_in_supply",
        name="Methanol (SMR-BF)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.CH3OHSYN_B,
            PtxboaProcessTypes.CH3OH_SB_B,
            PtxboaProcessTypes.CH3OH_S_B,
        ),
    )
    CH3OH_L_SMR_52_CH3OHSYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CH3OH-L__SMR_52%_CH3OHSYN__prod_in_demand",
        name="Methanol (SMR)*",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.CH3OHSYN_B,
        ),
    )
    CH3OH_L_SMR_52_CH3OHSYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CH3OH-L__SMR_52%_CH3OHSYN__prod_in_supply",
        name="Methanol (SMR)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.CH3OHSYN_B,
            PtxboaProcessTypes.CH3OH_SB_B,
            PtxboaProcessTypes.CH3OH_S_B,
        ),
    )
    CHX_L_ATR_91_EFUELSYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CHX-L__ATR_91%_EFUELSYN__prod_in_demand",
        name="FT-fuel (ATR)*",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.EFUELSYN_B,
        ),
    )
    CHX_L_ATR_91_EFUELSYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CHX-L__ATR_91%_EFUELSYN__prod_in_supply",
        name="FT-fuel (ATR)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.EFUELSYN_B,
            PtxboaProcessTypes.SYN_SB_B,
            PtxboaProcessTypes.SYN_S_B,
        ),
    )
    CHX_L_EFUELSYNC_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CHX-L__EFUELSYNC__prod_in_demand",
        name="FT-fuel (NG-based)*",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.EFUELSYNC_B,
        ),
    )
    CHX_L_EFUELSYNC_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CHX-L__EFUELSYNC__prod_in_supply",
        name="FT-fuel (NG-based)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.EFUELSYNC_B,
            PtxboaProcessTypes.SYN_SB_B,
            PtxboaProcessTypes.SYN_S_B,
        ),
    )
    CHX_L_SMR_52_BF_EFUELSYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CHX-L__SMR_52%_BF_EFUELSYN__prod_in_demand",
        name="FT-fuel (SMR-BF)*",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.EFUELSYN_B,
        ),
    )
    CHX_L_SMR_52_BF_EFUELSYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CHX-L__SMR_52%_BF_EFUELSYN__prod_in_supply",
        name="FT-fuel (SMR-BF)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.EFUELSYN_B,
            PtxboaProcessTypes.SYN_SB_B,
            PtxboaProcessTypes.SYN_S_B,
        ),
    )
    CHX_L_SMR_52_EFUELSYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="CHX-L__SMR_52%_EFUELSYN__prod_in_demand",
        name="FT-fuel (SMR)*",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.EFUELSYN_B,
        ),
    )
    CHX_L_SMR_52_EFUELSYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="CHX-L__SMR_52%_EFUELSYN__prod_in_supply",
        name="FT-fuel (SMR)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.EFUELSYN_B,
            PtxboaProcessTypes.SYN_SB_B,
            PtxboaProcessTypes.SYN_S_B,
        ),
    )
    DRI_S_ATR_91_DRI_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="DRI-S__ATR_91%_DRI__prod_in_demand",
        name="Direct Reduced Iron (ATR)*",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.DRI_B,
        ),
    )
    DRI_S_ATR_91_DRI_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="DRI-S__ATR_91%_DRI__prod_in_supply",
        name="Direct Reduced Iron (ATR)",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.DRI_SB_B,
        ),
    )
    DRI_S_NG_DRI_C_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="DRI-S__NG-DRI-C__prod_in_demand",
        name="Direct Reduced Iron (NG-based)*",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.NG_DRI_C_B,
        ),
    )
    DRI_S_NG_DRI_C_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="DRI-S__NG-DRI-C__prod_in_supply",
        name="Direct Reduced Iron (NG-based)",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.NG_DRI_C_B,
            PtxboaProcessTypes.DRI_SB_B,
        ),
    )
    DRI_S_SMR_52_BF_DRI_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="DRI-S__SMR_52%_BF_DRI__prod_in_demand",
        name="Direct Reduced Iron (SMR-BF)*",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.DRI_B,
        ),
    )
    DRI_S_SMR_52_BF_DRI_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="DRI-S__SMR_52%_BF_DRI__prod_in_supply",
        name="Direct Reduced Iron (SMR-BF)",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.DRI_SB_B,
        ),
    )
    DRI_S_SMR_52_DRI_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="DRI-S__SMR_52%_DRI__prod_in_demand",
        name="Direct Reduced Iron (SMR)*",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.DRI_B,
        ),
    )
    DRI_S_SMR_52_DRI_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="DRI-S__SMR_52%_DRI__prod_in_supply",
        name="Direct Reduced Iron (SMR)",
        flow_type_out=PtxboaFlowTypes.B_DRI_S,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.DRI_SB_B,
        ),
    )
    H2_G_ATR_91_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="H2-G__ATR_91%__prod_in_demand",
        name="Hydrogen (ATR)*",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.ATR_91_B,
        ),
    )
    H2_G_ATR_91_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="H2-G__ATR_91%__prod_in_supply",
        name="Hydrogen (ATR)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.H2_LIQ_B,
            PtxboaProcessTypes.H2_COMP_B,
            PtxboaProcessTypes.H2_RGAS_B,
            PtxboaProcessTypes.H2_SB_B,
            PtxboaProcessTypes.H2_S_B,
            PtxboaProcessTypes.H2_P_S_B,
            PtxboaProcessTypes.H2_P_L_B,
            PtxboaProcessTypes.H2_P_SR_B,
            PtxboaProcessTypes.H2_P_LR_B,
        ),
    )
    H2_G_ATR_91_PROD_IN_SUPPLY_TRANSPORT_NH3_L = PtxboaChainBlueTemplate(
        code="H2-G__ATR_91%__prod_in_supply__transport_NH3-L",
        name="Ammonia (ATR) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.NH3SYN_B,
            PtxboaProcessTypes.NH3_SB_B,
            PtxboaProcessTypes.NH3_S_B,
            PtxboaProcessTypes.NH3_REC_B,
        ),
    )
    H2_G_SMR_52_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="H2-G__SMR_52%__prod_in_demand",
        name="Hydrogen (SMR)*",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_B,
        ),
    )
    H2_G_SMR_52_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="H2-G__SMR_52%__prod_in_supply",
        name="Hydrogen (SMR)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.H2_LIQ_B,
            PtxboaProcessTypes.H2_COMP_B,
            PtxboaProcessTypes.H2_RGAS_B,
            PtxboaProcessTypes.H2_SB_B,
            PtxboaProcessTypes.H2_S_B,
            PtxboaProcessTypes.H2_P_S_B,
            PtxboaProcessTypes.H2_P_L_B,
            PtxboaProcessTypes.H2_P_SR_B,
            PtxboaProcessTypes.H2_P_LR_B,
        ),
    )
    H2_G_SMR_52_PROD_IN_SUPPLY_TRANSPORT_NH3_L = PtxboaChainBlueTemplate(
        code="H2-G__SMR_52%__prod_in_supply__transport_NH3-L",
        name="Ammonia (SMR) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.NH3SYN_B,
            PtxboaProcessTypes.NH3_SB_B,
            PtxboaProcessTypes.NH3_S_B,
            PtxboaProcessTypes.NH3_REC_B,
        ),
    )
    H2_G_SMR_52_BF_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="H2-G__SMR_52%_BF__prod_in_demand",
        name="Hydrogen (SMR-BF)*",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_BF_B,
        ),
    )
    H2_G_SMR_52_BF_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="H2-G__SMR_52%_BF__prod_in_supply",
        name="Hydrogen (SMR-BF)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.H2_LIQ_B,
            PtxboaProcessTypes.H2_COMP_B,
            PtxboaProcessTypes.H2_RGAS_B,
            PtxboaProcessTypes.H2_SB_B,
            PtxboaProcessTypes.H2_S_B,
            PtxboaProcessTypes.H2_P_S_B,
            PtxboaProcessTypes.H2_P_L_B,
            PtxboaProcessTypes.H2_P_SR_B,
            PtxboaProcessTypes.H2_P_LR_B,
        ),
    )
    H2_G_SMR_52_BF_PROD_IN_SUPPLY_TRANSPORT_NH3_L = PtxboaChainBlueTemplate(
        code="H2-G__SMR_52%_BF__prod_in_supply__transport_NH3-L",
        name="Ammonia (SMR-BF) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.NH3SYN_B,
            PtxboaProcessTypes.NH3_SB_B,
            PtxboaProcessTypes.NH3_S_B,
            PtxboaProcessTypes.NH3_REC_B,
        ),
    )
    NH3_L_ATR_91_NH3SYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="NH3-L__ATR_91%_NH3SYN__prod_in_demand",
        name="Ammonia (ATR)*",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.NH3SYN_B,
        ),
    )
    NH3_L_ATR_91_NH3SYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="NH3-L__ATR_91%_NH3SYN__prod_in_supply",
        name="Ammonia (ATR)",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.NH3SYN_B,
            PtxboaProcessTypes.NH3_SB_B,
            PtxboaProcessTypes.NH3_S_B,
        ),
    )
    NH3_L_SMR_52_BF_NH3SYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="NH3-L__SMR_52%_BF_NH3SYN__prod_in_demand",
        name="Ammonia (SMR-BF)*",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.NH3SYN_B,
        ),
    )
    NH3_L_SMR_52_BF_NH3SYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="NH3-L__SMR_52%_BF_NH3SYN__prod_in_supply",
        name="Ammonia (SMR-BF)",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.NH3SYN_B,
            PtxboaProcessTypes.NH3_SB_B,
            PtxboaProcessTypes.NH3_S_B,
        ),
    )
    NH3_L_SMR_52_NH3SYN_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="NH3-L__SMR_52%_NH3SYN__prod_in_demand",
        name="Ammonia (SMR)*",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.NH3SYN_B,
        ),
    )
    NH3_L_SMR_52_NH3SYN_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="NH3-L__SMR_52%_NH3SYN__prod_in_supply",
        name="Ammonia (SMR)",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.NH3SYN_B,
            PtxboaProcessTypes.NH3_SB_B,
            PtxboaProcessTypes.NH3_S_B,
        ),
    )
    STL_S_ATR_91_DRI_EAF_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="STL-S__ATR_91%_DRI_EAF__prod_in_demand",
        name="Crude Steel (ATR)*",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_ATR_91_DRI_EAF_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="STL-S__ATR_91%_DRI_EAF__prod_in_supply",
        name="Crude Steel (ATR)",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.ATR_91_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.DRI_SB_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_NG_DRI_C_EAF_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="STL-S__NG-DRI-C_EAF__prod_in_demand",
        name="Crude Steel (NG-based)*",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.NG_DRI_C_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_NG_DRI_C_EAF_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="STL-S__NG-DRI-C_EAF__prod_in_supply",
        name="Crude Steel (NG-based)",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.NG_DRI_C_B,
            PtxboaProcessTypes.DRI_SB_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_SMR_52_BF_DRI_EAF_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="STL-S__SMR_52%_BF_DRI_EAF__prod_in_demand",
        name="Crude Steel (SMR-BF)*",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_SMR_52_BF_DRI_EAF_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="STL-S__SMR_52%_BF_DRI_EAF__prod_in_supply",
        name="Crude Steel (SMR-BF)",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.SMR_52_BF_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.DRI_SB_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_SMR_52_DRI_EAF_PROD_IN_DEMAND = PtxboaChainBlueTemplate(
        code="STL-S__SMR_52%_DRI_EAF__prod_in_demand",
        name="Crude Steel (SMR)*",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.CH4_LIQ_B,
            PtxboaProcessTypes.CH4_COMP_B,
            PtxboaProcessTypes.CH4_RGAS_B,
            PtxboaProcessTypes.CH4_SB_B,
            PtxboaProcessTypes.CH4_S_B,
            PtxboaProcessTypes.CH4_P_S_B,
            PtxboaProcessTypes.CH4_P_L_B,
            PtxboaProcessTypes.CH4_P_SR_B,
            PtxboaProcessTypes.CH4_P_LR_B,
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    STL_S_SMR_52_DRI_EAF_PROD_IN_SUPPLY = PtxboaChainBlueTemplate(
        code="STL-S__SMR_52%_DRI_EAF__prod_in_supply",
        name="Crude Steel (SMR)",
        flow_type_out=PtxboaFlowTypes.STL_S,
        process_types=(
            PtxboaProcessTypes.SMR_52_B,
            PtxboaProcessTypes.DRI_B,
            PtxboaProcessTypes.DRI_SB_B,
            PtxboaProcessTypes.EAF_B,
        ),
    )
    AMMONIA_AEL_ = PtxboaChainGreenTemplate(
        code="Ammonia (AEL)",
        name="Ammonia (AEL)",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.NH3SYN,
            PtxboaProcessTypes.NH3_SB,
            PtxboaProcessTypes.NH3_S,
        ),
    )
    AMMONIA_AEL_RECONV_TO_H2 = PtxboaChainGreenTemplate(
        code="Ammonia (AEL) + reconv. to H2",
        name="Ammonia (AEL) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.NH3SYN,
            PtxboaProcessTypes.NH3_REC,
            PtxboaProcessTypes.NH3_REC,
            PtxboaProcessTypes.NH3_SB,
            PtxboaProcessTypes.NH3_S,
        ),
    )
    AMMONIA_PEM_ = PtxboaChainGreenTemplate(
        code="Ammonia (PEM)",
        name="Ammonia (PEM)",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.NH3SYN,
            PtxboaProcessTypes.NH3_SB,
            PtxboaProcessTypes.NH3_S,
        ),
    )
    AMMONIA_PEM_RECONV_TO_H2 = PtxboaChainGreenTemplate(
        code="Ammonia (PEM) + reconv. to H2",
        name="Ammonia (PEM) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.NH3SYN,
            PtxboaProcessTypes.NH3_REC,
            PtxboaProcessTypes.NH3_REC,
            PtxboaProcessTypes.NH3_SB,
            PtxboaProcessTypes.NH3_S,
        ),
    )
    AMMONIA_SOEC_ = PtxboaChainGreenTemplate(
        code="Ammonia (SOEC)",
        name="Ammonia (SOEC)",
        flow_type_out=PtxboaFlowTypes.NH3_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.NH3SYN,
            PtxboaProcessTypes.NH3_SB,
            PtxboaProcessTypes.NH3_S,
        ),
    )
    AMMONIA_SOEC_RECONV_TO_H2 = PtxboaChainGreenTemplate(
        code="Ammonia (SOEC) + reconv. to H2",
        name="Ammonia (SOEC) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.NH3SYN,
            PtxboaProcessTypes.NH3_REC,
            PtxboaProcessTypes.NH3_REC,
            PtxboaProcessTypes.NH3_SB,
            PtxboaProcessTypes.NH3_S,
        ),
    )
    FT_E_FUELS_AEL_ = PtxboaChainGreenTemplate(
        code="FT e-fuels (AEL)",
        name="FT e-fuels (AEL)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.EFUELSYN,
            PtxboaProcessTypes.SYN_SB,
            PtxboaProcessTypes.SYN_S,
        ),
    )
    FT_E_FUELS_PEM_ = PtxboaChainGreenTemplate(
        code="FT e-fuels (PEM)",
        name="FT e-fuels (PEM)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.EFUELSYN,
            PtxboaProcessTypes.SYN_SB,
            PtxboaProcessTypes.SYN_S,
        ),
    )
    FT_E_FUELS_SOEC_ = PtxboaChainGreenTemplate(
        code="FT e-fuels (SOEC)",
        name="FT e-fuels (SOEC)",
        flow_type_out=PtxboaFlowTypes.CHX_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.EFUELSYN,
            PtxboaProcessTypes.SYN_SB,
            PtxboaProcessTypes.SYN_S,
        ),
    )
    GREEN_IRON_AEL_ = PtxboaChainGreenTemplate(
        code="Green Iron (AEL)",
        name="Green Iron (AEL)",
        flow_type_out=PtxboaFlowTypes.DRI_S,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.DRI,
            PtxboaProcessTypes.DRI_SB,
        ),
    )
    GREEN_IRON_PEM_ = PtxboaChainGreenTemplate(
        code="Green Iron (PEM)",
        name="Green Iron (PEM)",
        flow_type_out=PtxboaFlowTypes.DRI_S,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.DRI,
            PtxboaProcessTypes.DRI_SB,
        ),
    )
    GREEN_IRON_SOEC_ = PtxboaChainGreenTemplate(
        code="Green Iron (SOEC)",
        name="Green Iron (SOEC)",
        flow_type_out=PtxboaFlowTypes.DRI_S,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.DRI,
            PtxboaProcessTypes.DRI_SB,
        ),
    )
    HYDROGEN_AEL_ = PtxboaChainGreenTemplate(
        code="Hydrogen (AEL)",
        name="Hydrogen (AEL)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_LIQ,
            PtxboaProcessTypes.H2_COMP,
            PtxboaProcessTypes.H2_RGAS,
            PtxboaProcessTypes.H2_SB,
            PtxboaProcessTypes.H2_S,
            PtxboaProcessTypes.H2_P_S,
            PtxboaProcessTypes.H2_P_L,
            PtxboaProcessTypes.H2_P_SR,
            PtxboaProcessTypes.H2_P_LR,
        ),
    )
    HYDROGEN_PEM_ = PtxboaChainGreenTemplate(
        code="Hydrogen (PEM)",
        name="Hydrogen (PEM)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_LIQ,
            PtxboaProcessTypes.H2_COMP,
            PtxboaProcessTypes.H2_RGAS,
            PtxboaProcessTypes.H2_SB,
            PtxboaProcessTypes.H2_S,
            PtxboaProcessTypes.H2_P_S,
            PtxboaProcessTypes.H2_P_L,
            PtxboaProcessTypes.H2_P_SR,
            PtxboaProcessTypes.H2_P_LR,
        ),
    )
    HYDROGEN_SOEC_ = PtxboaChainGreenTemplate(
        code="Hydrogen (SOEC)",
        name="Hydrogen (SOEC)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_LIQ,
            PtxboaProcessTypes.H2_COMP,
            PtxboaProcessTypes.H2_RGAS,
            PtxboaProcessTypes.H2_SB,
            PtxboaProcessTypes.H2_S,
            PtxboaProcessTypes.H2_P_S,
            PtxboaProcessTypes.H2_P_L,
            PtxboaProcessTypes.H2_P_SR,
            PtxboaProcessTypes.H2_P_LR,
        ),
    )
    LOHC_AEL_ = PtxboaChainGreenTemplate(
        code="LOHC (AEL)",
        name="LOHC (AEL)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.LOHC_CON,
            PtxboaProcessTypes.LOHC_REC,
            PtxboaProcessTypes.LOHC_SB,
            PtxboaProcessTypes.LOHC_S,
        ),
    )
    LOHC_PEM_ = PtxboaChainGreenTemplate(
        code="LOHC (PEM)",
        name="LOHC (PEM)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.LOHC_CON,
            PtxboaProcessTypes.LOHC_REC,
            PtxboaProcessTypes.LOHC_SB,
            PtxboaProcessTypes.LOHC_S,
        ),
    )
    LOHC_SOEC_ = PtxboaChainGreenTemplate(
        code="LOHC (SOEC)",
        name="LOHC (SOEC)",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.LOHC_CON,
            PtxboaProcessTypes.LOHC_REC,
            PtxboaProcessTypes.LOHC_SB,
            PtxboaProcessTypes.LOHC_S,
        ),
    )
    METHANE_AEL_ = PtxboaChainGreenTemplate(
        code="Methane (AEL)",
        name="Methane (AEL)",
        flow_type_out=PtxboaFlowTypes.CH4_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH4SYN,
            PtxboaProcessTypes.CH4_LIQ,
            PtxboaProcessTypes.CH4_COMP,
            PtxboaProcessTypes.CH4_RGAS,
            PtxboaProcessTypes.CH4_SB,
            PtxboaProcessTypes.CH4_S,
            PtxboaProcessTypes.CH4_P_S,
            PtxboaProcessTypes.CH4_P_L,
            PtxboaProcessTypes.CH4_P_SR,
            PtxboaProcessTypes.CH4_P_LR,
        ),
    )
    METHANE_AEL_RECONV_TO_H2 = PtxboaChainGreenTemplate(
        code="Methane (AEL) + reconv. to H2",
        name="Methane (AEL) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH4SYN,
            PtxboaProcessTypes.CH4_LIQ,
            PtxboaProcessTypes.CH4_COMP,
            PtxboaProcessTypes.REGASATR,
            PtxboaProcessTypes.ATR,
            PtxboaProcessTypes.CH4_SB,
            PtxboaProcessTypes.CH4_S,
            PtxboaProcessTypes.CH4_P_S,
            PtxboaProcessTypes.CH4_P_L,
            PtxboaProcessTypes.CH4_P_SR,
            PtxboaProcessTypes.CH4_P_LR,
        ),
    )
    METHANE_PEM_ = PtxboaChainGreenTemplate(
        code="Methane (PEM)",
        name="Methane (PEM)",
        flow_type_out=PtxboaFlowTypes.CH4_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH4SYN,
            PtxboaProcessTypes.CH4_LIQ,
            PtxboaProcessTypes.CH4_COMP,
            PtxboaProcessTypes.CH4_RGAS,
            PtxboaProcessTypes.CH4_SB,
            PtxboaProcessTypes.CH4_S,
            PtxboaProcessTypes.CH4_P_S,
            PtxboaProcessTypes.CH4_P_L,
            PtxboaProcessTypes.CH4_P_SR,
            PtxboaProcessTypes.CH4_P_LR,
        ),
    )
    METHANE_PEM_RECONV_TO_H2 = PtxboaChainGreenTemplate(
        code="Methane (PEM) + reconv. to H2",
        name="Methane (PEM) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH4SYN,
            PtxboaProcessTypes.CH4_LIQ,
            PtxboaProcessTypes.CH4_COMP,
            PtxboaProcessTypes.REGASATR,
            PtxboaProcessTypes.ATR,
            PtxboaProcessTypes.CH4_SB,
            PtxboaProcessTypes.CH4_S,
            PtxboaProcessTypes.CH4_P_S,
            PtxboaProcessTypes.CH4_P_L,
            PtxboaProcessTypes.CH4_P_SR,
            PtxboaProcessTypes.CH4_P_LR,
        ),
    )
    METHANE_SOEC_ = PtxboaChainGreenTemplate(
        code="Methane (SOEC)",
        name="Methane (SOEC)",
        flow_type_out=PtxboaFlowTypes.CH4_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH4SYN,
            PtxboaProcessTypes.CH4_LIQ,
            PtxboaProcessTypes.CH4_COMP,
            PtxboaProcessTypes.CH4_RGAS,
            PtxboaProcessTypes.CH4_SB,
            PtxboaProcessTypes.CH4_S,
            PtxboaProcessTypes.CH4_P_S,
            PtxboaProcessTypes.CH4_P_L,
            PtxboaProcessTypes.CH4_P_SR,
            PtxboaProcessTypes.CH4_P_LR,
        ),
    )
    METHANE_SOEC_RECONV_TO_H2 = PtxboaChainGreenTemplate(
        code="Methane (SOEC) + reconv. to H2",
        name="Methane (SOEC) + reconv. to H2",
        flow_type_out=PtxboaFlowTypes.H2_G,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH4SYN,
            PtxboaProcessTypes.CH4_LIQ,
            PtxboaProcessTypes.CH4_COMP,
            PtxboaProcessTypes.REGASATR,
            PtxboaProcessTypes.ATR,
            PtxboaProcessTypes.CH4_SB,
            PtxboaProcessTypes.CH4_S,
            PtxboaProcessTypes.CH4_P_S,
            PtxboaProcessTypes.CH4_P_L,
            PtxboaProcessTypes.CH4_P_SR,
            PtxboaProcessTypes.CH4_P_LR,
        ),
    )
    METHANOL_AEL_ = PtxboaChainGreenTemplate(
        code="Methanol (AEL)",
        name="Methanol (AEL)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.AEL_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH3OHSYN,
            PtxboaProcessTypes.CH3OH_SB,
            PtxboaProcessTypes.CH3OH_S,
        ),
    )
    METHANOL_PEM_ = PtxboaChainGreenTemplate(
        code="Methanol (PEM)",
        name="Methanol (PEM)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.PEM_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH3OHSYN,
            PtxboaProcessTypes.CH3OH_SB,
            PtxboaProcessTypes.CH3OH_S,
        ),
    )
    METHANOL_SOEC_ = PtxboaChainGreenTemplate(
        code="Methanol (SOEC)",
        name="Methanol (SOEC)",
        flow_type_out=PtxboaFlowTypes.CH3OH_L,
        process_types=(
            PtxboaProcessTypes.EL_STR,
            PtxboaProcessTypes.SOEC_EL,
            PtxboaProcessTypes.H2_STR,
            PtxboaProcessTypes.CH3OHSYN,
            PtxboaProcessTypes.CH3OH_SB,
            PtxboaProcessTypes.CH3OH_S,
        ),
    )
