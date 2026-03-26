"""DO NOT EDIT (created by classes/_update.py)."""

from ptxboa.classes.base import PtxboaFlow, PtxboaParameter, PtxboaProcess, PtxboaRegion


class PtxboaParameters:
    CALOR = PtxboaParameter._create_subclass(
        "PtxboaParameterCALOR",
        code="CALOR",
        name="calorific values",
        template_class_name="PtxboaParameter",
    )
    CAPEX = PtxboaParameter._create_subclass(
        "PtxboaParameterCAPEX",
        code="CAPEX",
        name="CAPEX",
        template_class_name="PtxboaParameter",
    )
    CAP_T = PtxboaParameter._create_subclass(
        "PtxboaParameterCAP_T",
        code="CAP-T",
        name="transport capacity",
        template_class_name="PtxboaParameter",
    )
    CBOUND = PtxboaParameter._create_subclass(
        "PtxboaParameterCBOUND",
        code="CBOUND",
        name="C bound in product",
        template_class_name="PtxboaParameter",
    )
    CH4SHARE = PtxboaParameter._create_subclass(
        "PtxboaParameterCH4SHARE",
        code="CH4SHARE",
        name="methane share",
        template_class_name="PtxboaParameter",
    )
    CO2CPT_R = PtxboaParameter._create_subclass(
        "PtxboaParameterCO2CPT_R",
        code="CO2CPT-R",
        name="capture rate by flow",
        template_class_name="PtxboaParameter",
    )
    CO2CPT_S = PtxboaParameter._create_subclass(
        "PtxboaParameterCO2CPT_S",
        code="CO2CPT-S",
        name="CO2 for capture share",
        template_class_name="PtxboaParameter",
    )
    CONV = PtxboaParameter._create_subclass(
        "PtxboaParameterCONV",
        code="CONV",
        name="conversion factors",
        template_class_name="PtxboaParameter",
    )
    CONV_OT = PtxboaParameter._create_subclass(
        "PtxboaParameterCONV_OT",
        code="CONV-OT",
        name="conversion factors (other fuel, transport)",
        template_class_name="PtxboaParameter",
    )
    DST_S_D = PtxboaParameter._create_subclass(
        "PtxboaParameterDST_S_D",
        code="DST-S-D",
        name="shipping distance",
        template_class_name="PtxboaParameter",
    )
    DST_S_DP = PtxboaParameter._create_subclass(
        "PtxboaParameterDST_S_DP",
        code="DST-S-DP",
        name="pipeline distance",
        template_class_name="PtxboaParameter",
    )
    EF_E = PtxboaParameter._create_subclass(
        "PtxboaParameterEF_E",
        code="EF_E",
        name="emission factor for emission balance",
        template_class_name="PtxboaParameter",
    )
    EF_M = PtxboaParameter._create_subclass(
        "PtxboaParameterEF_M",
        code="EF_M",
        name="emission factor for mass balance",
        template_class_name="PtxboaParameter",
    )
    EFF = PtxboaParameter._create_subclass(
        "PtxboaParameterEFF",
        code="EFF",
        name="efficiency",
        template_class_name="PtxboaParameter",
    )
    FLH = PtxboaParameter._create_subclass(
        "PtxboaParameterFLH",
        code="FLH",
        name="full load hours",
        template_class_name="PtxboaParameter",
    )
    LIFETIME = PtxboaParameter._create_subclass(
        "PtxboaParameterLIFETIME",
        code="LIFETIME",
        name="lifetime / amortization period",
        template_class_name="PtxboaParameter",
    )
    LOSS = PtxboaParameter._create_subclass(
        "PtxboaParameterLOSS",
        code="LOSS",
        name="losses (own fuel)",
        template_class_name="PtxboaParameter",
    )
    LOSS_T = PtxboaParameter._create_subclass(
        "PtxboaParameterLOSS_T",
        code="LOSS-T",
        name="losses (own fuel, transport)",
        template_class_name="PtxboaParameter",
    )
    OPEX_F = PtxboaParameter._create_subclass(
        "PtxboaParameterOPEX_F",
        code="OPEX-F",
        name="OPEX (fix)",
        template_class_name="PtxboaParameter",
    )
    OPEX_O = PtxboaParameter._create_subclass(
        "PtxboaParameterOPEX_O",
        code="OPEX-O",
        name="OPEX (other variable)",
        template_class_name="PtxboaParameter",
    )
    OPEX_T = PtxboaParameter._create_subclass(
        "PtxboaParameterOPEX_T",
        code="OPEX-T",
        name="levelized costs",
        template_class_name="PtxboaParameter",
    )
    SEASHARE = PtxboaParameter._create_subclass(
        "PtxboaParameterSEASHARE",
        code="SEASHARE",
        name="sea share of pipeline distance",
        template_class_name="PtxboaParameter",
    )
    SPECCOST = PtxboaParameter._create_subclass(
        "PtxboaParameterSPECCOST",
        code="SPECCOST",
        name="specific costs",
        template_class_name="PtxboaParameter",
    )
    WACC = PtxboaParameter._create_subclass(
        "PtxboaParameterWACC",
        code="WACC",
        name="WACC",
        template_class_name="PtxboaParameter",
    )


class PtxboaProcesss:
    AEL_EL = PtxboaProcess._create_subclass(
        "PtxboaProcessAEL_EL",
        code="AEL-EL",
        name="AEL electrolysis",
        template_class_name="PtxboaProcess",
    )
    ATR = PtxboaProcess._create_subclass(
        "PtxboaProcessATR",
        code="ATR",
        name="Methane reconversion",
        template_class_name="PtxboaProcess",
    )
    ATR_91_B = PtxboaProcess._create_subclass(
        "PtxboaProcessATR_91_B",
        code="ATR_91%#B",
        name="autothermal reformer with 91% carbon capture (blue)",
        template_class_name="PtxboaProcess",
    )
    CCGT_CC_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCCGT_CC_B",
        code="CCGT-CC#B",
        name="Combined Cycle Gas Turbine with CCS (blue)",
        template_class_name="PtxboaProcess",
    )
    CH3OH_S = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OH_S",
        code="CH3OH-S",
        name="Methanol ship (own fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    CH3OH_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OH_S_B",
        code="CH3OH-S#B",
        name="Methanol ship (own fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    CH3OH_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OH_SB",
        code="CH3OH-SB",
        name="Methanol ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    CH3OH_SB_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OH_SB_B",
        code="CH3OH-SB#B",
        name="Methanol ship (bunker fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    CH3OHSYC_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OHSYC_B",
        code="CH3OHSYC#B",
        name="Methanol Synthesis classic route with CCS (blue)",
        template_class_name="PtxboaProcess",
    )
    CH3OHSYN = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OHSYN",
        code="CH3OHSYN",
        name="Methanol Synthesis",
        template_class_name="PtxboaProcess",
    )
    CH3OHSYN_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH3OHSYN_B",
        code="CH3OHSYN#B",
        name="Methanol Synthesis (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_COMP = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_COMP",
        code="CH4-COMP",
        name="Methane compression",
        template_class_name="PtxboaProcess",
    )
    CH4_COMP_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_COMP_B",
        code="CH4-COMP#B",
        name="Methane compression (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_LIQ = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_LIQ",
        code="CH4-LIQ",
        name="Methane Liquefaction",
        template_class_name="PtxboaProcess",
    )
    CH4_LIQ_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_LIQ_B",
        code="CH4-LIQ#B",
        name="Methane Liquefaction (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_P_L = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_L",
        code="CH4-P-L",
        name="Methane land pipeline new",
        template_class_name="PtxboaProcess",
    )
    CH4_P_L_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_L_B",
        code="CH4-P-L#B",
        name="Methane land pipeline new (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_P_LR = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_LR",
        code="CH4-P-LR",
        name="Methane land pipeline retrofitted",
        template_class_name="PtxboaProcess",
    )
    CH4_P_LR_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_LR_B",
        code="CH4-P-LR#B",
        name="Methane land pipeline retrofitted (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_P_S = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_S",
        code="CH4-P-S",
        name="Methane sea pipeline",
        template_class_name="PtxboaProcess",
    )
    CH4_P_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_S_B",
        code="CH4-P-S#B",
        name="Methane sea pipeline (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_P_SR = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_SR",
        code="CH4-P-SR",
        name="Methane sea pipeline retrofitted",
        template_class_name="PtxboaProcess",
    )
    CH4_P_SR_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_P_SR_B",
        code="CH4-P-SR#B",
        name="Methane sea pipeline retrofitted (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_RGAS = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_RGAS",
        code="CH4-RGAS",
        name="Methane Regasification",
        template_class_name="PtxboaProcess",
    )
    CH4_RGAS_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_RGAS_B",
        code="CH4-RGAS#B",
        name="Methane Regasification (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_S = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_S",
        code="CH4-S",
        name="LNG ship (own fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    CH4_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_S_B",
        code="CH4-S#B",
        name="LNG ship (own fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_SB",
        code="CH4-SB",
        name="LNG ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    CH4_SB_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4_SB_B",
        code="CH4-SB#B",
        name="LNG ship (bunker fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    CH4SYN = PtxboaProcess._create_subclass(
        "PtxboaProcessCH4SYN",
        code="CH4SYN",
        name="Methane Synthesis",
        template_class_name="PtxboaProcess",
    )
    CO2_T_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessCO2_T_S_B",
        code="CO2-T+S#B",
        name="CO2 transport and storage (blue)",
        template_class_name="PtxboaProcess",
    )
    DAC = PtxboaProcess._create_subclass(
        "PtxboaProcessDAC",
        code="DAC",
        name="Direct Air Capture",
        template_class_name="PtxboaProcess",
    )
    DAC_B = PtxboaProcess._create_subclass(
        "PtxboaProcessDAC_B",
        code="DAC#B",
        name="Direct Air Capture (blue)",
        template_class_name="PtxboaProcess",
    )
    DESAL = PtxboaProcess._create_subclass(
        "PtxboaProcessDESAL",
        code="DESAL",
        name="Sea Water desalination",
        template_class_name="PtxboaProcess",
    )
    DRI = PtxboaProcess._create_subclass(
        "PtxboaProcessDRI",
        code="DRI",
        name="Green iron reduction",
        template_class_name="PtxboaProcess",
    )
    DRI_B = PtxboaProcess._create_subclass(
        "PtxboaProcessDRI_B",
        code="DRI#B",
        name="Green iron reduction (blue)",
        template_class_name="PtxboaProcess",
    )
    DRI_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessDRI_SB",
        code="DRI-SB",
        name="Green iron ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    DRI_SB_B = PtxboaProcess._create_subclass(
        "PtxboaProcessDRI_SB_B",
        code="DRI-SB#B",
        name="Green iron ship (bunker fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    EAF_B = PtxboaProcess._create_subclass(
        "PtxboaProcessEAF_B",
        code="EAF#B",
        name="electric arc furnance (blue)",
        template_class_name="PtxboaProcess",
    )
    EFUELSYN = PtxboaProcess._create_subclass(
        "PtxboaProcessEFUELSYN",
        code="EFUELSYN",
        name="FT e-fuels Synthesis (Fischer-Tropsch)",
        template_class_name="PtxboaProcess",
    )
    EFUELSYN_B = PtxboaProcess._create_subclass(
        "PtxboaProcessEFUELSYN_B",
        code="EFUELSYN#B",
        name="FT e-fuels Synthesis (Fischer-Tropsch) (blue)",
        template_class_name="PtxboaProcess",
    )
    EFUELSYNC_B = PtxboaProcess._create_subclass(
        "PtxboaProcessEFUELSYNC_B",
        code="EFUELSYNC#B",
        name="FT Synthesis (Fischer-Tropsch) using NG with CCS (blue)",
        template_class_name="PtxboaProcess",
    )
    EL_STR = PtxboaProcess._create_subclass(
        "PtxboaProcessEL_STR",
        code="EL-STR",
        name="electricity storage",
        template_class_name="PtxboaProcess",
    )
    H2_COMP = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_COMP",
        code="H2-COMP",
        name="Hydrogen compression",
        template_class_name="PtxboaProcess",
    )
    H2_COMP_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_COMP_B",
        code="H2-COMP#B",
        name="Hydrogen compression (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_LIQ = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_LIQ",
        code="H2-LIQ",
        name="Hydrogen Liquefaction",
        template_class_name="PtxboaProcess",
    )
    H2_LIQ_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_LIQ_B",
        code="H2-LIQ#B",
        name="Hydrogen Liquefaction (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_P_L = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_L",
        code="H2-P-L",
        name="Hydrogen land pipeline new",
        template_class_name="PtxboaProcess",
    )
    H2_P_L_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_L_B",
        code="H2-P-L#B",
        name="Hydrogen land pipeline new (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_P_LR = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_LR",
        code="H2-P-LR",
        name="Hydrogen land pipeline retrofitted",
        template_class_name="PtxboaProcess",
    )
    H2_P_LR_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_LR_B",
        code="H2-P-LR#B",
        name="Hydrogen land pipeline retrofitted (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_P_S = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_S",
        code="H2-P-S",
        name="Hydrogen sea pipeline",
        template_class_name="PtxboaProcess",
    )
    H2_P_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_S_B",
        code="H2-P-S#B",
        name="Hydrogen sea pipeline (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_P_SR = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_SR",
        code="H2-P-SR",
        name="Hydrogen sea pipeline retrofitted",
        template_class_name="PtxboaProcess",
    )
    H2_P_SR_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_P_SR_B",
        code="H2-P-SR#B",
        name="Hydrogen sea pipeline retrofitted (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_RGAS = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_RGAS",
        code="H2-RGAS",
        name="Hydrogen Regasification",
        template_class_name="PtxboaProcess",
    )
    H2_RGAS_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_RGAS_B",
        code="H2-RGAS#B",
        name="Hydrogen Regasification (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_S = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_S",
        code="H2-S",
        name="Hydrogen ship (own fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    H2_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_S_B",
        code="H2-S#B",
        name="Hydrogen ship (own fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_SB",
        code="H2-SB",
        name="Hydrogen ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    H2_SB_B = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_SB_B",
        code="H2-SB#B",
        name="Hydrogen ship (bunker fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    H2_STR = PtxboaProcess._create_subclass(
        "PtxboaProcessH2_STR",
        code="H2-STR",
        name="Hydrogen storage",
        template_class_name="PtxboaProcess",
    )
    HEATPUMP_B = PtxboaProcess._create_subclass(
        "PtxboaProcessHEATPUMP_B",
        code="HEATPUMP#B",
        name="Large scale Heatpump (blue)",
        template_class_name="PtxboaProcess",
    )
    LOHC_CON = PtxboaProcess._create_subclass(
        "PtxboaProcessLOHC_CON",
        code="LOHC-CON",
        name="LOHC conversion",
        template_class_name="PtxboaProcess",
    )
    LOHC_REC = PtxboaProcess._create_subclass(
        "PtxboaProcessLOHC_REC",
        code="LOHC-REC",
        name="LOHC reconversion",
        template_class_name="PtxboaProcess",
    )
    LOHC_S = PtxboaProcess._create_subclass(
        "PtxboaProcessLOHC_S",
        code="LOHC-S",
        name="LOHC ship (own fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    LOHC_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessLOHC_SB",
        code="LOHC-SB",
        name="LOHC ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    NG_DRI_C_B = PtxboaProcess._create_subclass(
        "PtxboaProcessNG_DRI_C_B",
        code="NG-DRI-C#B",
        name="NG-based iron reduction with CCS (blue)",
        template_class_name="PtxboaProcess",
    )
    NG_PROD_B = PtxboaProcess._create_subclass(
        "PtxboaProcessNG_PROD_B",
        code="NG-PROD#B",
        name="production of natural gas (blue)",
        template_class_name="PtxboaProcess",
    )
    NH3_REC = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3_REC",
        code="NH3-REC",
        name="Ammonia reconversion",
        template_class_name="PtxboaProcess",
    )
    NH3_REC_B = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3_REC_B",
        code="NH3-REC#B",
        name="Ammonia reconversion (blue)",
        template_class_name="PtxboaProcess",
    )
    NH3_S = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3_S",
        code="NH3-S",
        name="Ammonia ship (own fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    NH3_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3_S_B",
        code="NH3-S#B",
        name="Ammonia ship (own fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    NH3_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3_SB",
        code="NH3-SB",
        name="Ammonia ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    NH3_SB_B = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3_SB_B",
        code="NH3-SB#B",
        name="Ammonia ship (bunker fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    NH3SYN = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3SYN",
        code="NH3SYN",
        name="Ammonia Synthesis (Haber-Bosch)",
        template_class_name="PtxboaProcess",
    )
    NH3SYN_B = PtxboaProcess._create_subclass(
        "PtxboaProcessNH3SYN_B",
        code="NH3SYN#B",
        name="Ammonia Synthesis (Haber-Bosch) (blue)",
        template_class_name="PtxboaProcess",
    )
    PEM_EL = PtxboaProcess._create_subclass(
        "PtxboaProcessPEM_EL",
        code="PEM-EL",
        name="PEM electrolysis",
        template_class_name="PtxboaProcess",
    )
    PV_FIX = PtxboaProcess._create_subclass(
        "PtxboaProcessPV_FIX",
        code="PV-FIX",
        name="PV tilted",
        template_class_name="PtxboaProcess",
    )
    REGASATR = PtxboaProcess._create_subclass(
        "PtxboaProcessREGASATR",
        code="REGASATR",
        name="Methane reconversion incl. regasification",
        template_class_name="PtxboaProcess",
    )
    RES_HYBR = PtxboaProcess._create_subclass(
        "PtxboaProcessRES_HYBR",
        code="RES-HYBR",
        name="Wind-PV-Hybrid",
        template_class_name="PtxboaProcess",
    )
    SMR_52_B = PtxboaProcess._create_subclass(
        "PtxboaProcessSMR_52_B",
        code="SMR_52%#B",
        name="steam methane reformer with 52% carbon capture (blue)",
        template_class_name="PtxboaProcess",
    )
    SMR_52_BF_B = PtxboaProcess._create_subclass(
        "PtxboaProcessSMR_52_BF_B",
        code="SMR_52%_BF#B",
        name="existing steam methane reformer with retrofit 52% carbon capture (blue)",
        template_class_name="PtxboaProcess",
    )
    SOEC_EL = PtxboaProcess._create_subclass(
        "PtxboaProcessSOEC_EL",
        code="SOEC-EL",
        name="SOEC (high-temp) electrolysis",
        template_class_name="PtxboaProcess",
    )
    SYN_S = PtxboaProcess._create_subclass(
        "PtxboaProcessSYN_S",
        code="SYN-S",
        name="FT e-fuels ship (own fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    SYN_S_B = PtxboaProcess._create_subclass(
        "PtxboaProcessSYN_S_B",
        code="SYN-S#B",
        name="FT e-fuels ship (own fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    SYN_SB = PtxboaProcess._create_subclass(
        "PtxboaProcessSYN_SB",
        code="SYN-SB",
        name="FT e-fuels ship (bunker fuel consumption)",
        template_class_name="PtxboaProcess",
    )
    SYN_SB_B = PtxboaProcess._create_subclass(
        "PtxboaProcessSYN_SB_B",
        code="SYN-SB#B",
        name="FT e-fuels ship (bunker fuel consumption) (blue)",
        template_class_name="PtxboaProcess",
    )
    WIND_OFF = PtxboaProcess._create_subclass(
        "PtxboaProcessWIND_OFF",
        code="WIND-OFF",
        name="Wind Offshore",
        template_class_name="PtxboaProcess",
    )
    WIND_ON = PtxboaProcess._create_subclass(
        "PtxboaProcessWIND_ON",
        code="WIND-ON",
        name="Wind Onshore",
        template_class_name="PtxboaProcess",
    )


class PtxboaFlows:
    B_DRI_S = PtxboaFlow._create_subclass(
        "PtxboaFlowB_DRI_S",
        code="B-DRI-S",
        name="Blue iron",
        template_class_name="PtxboaFlow",
    )
    BFUEL_L = PtxboaFlow._create_subclass(
        "PtxboaFlowBFUEL_L",
        code="BFUEL-L",
        name="bunker fuel",
        template_class_name="PtxboaFlow",
    )
    CH3OH_L = PtxboaFlow._create_subclass(
        "PtxboaFlowCH3OH_L",
        code="CH3OH-L",
        name="methanol (liquid)",
        template_class_name="PtxboaFlow",
    )
    CH4_G = PtxboaFlow._create_subclass(
        "PtxboaFlowCH4_G",
        code="CH4-G",
        name="methane (gas)",
        template_class_name="PtxboaFlow",
    )
    CH4_L = PtxboaFlow._create_subclass(
        "PtxboaFlowCH4_L",
        code="CH4-L",
        name="methane (liquid)",
        template_class_name="PtxboaFlow",
    )
    CHX_L = PtxboaFlow._create_subclass(
        "PtxboaFlowCHX_L",
        code="CHX-L",
        name="FT e-fuels",
        template_class_name="PtxboaFlow",
    )
    CO2_C = PtxboaFlow._create_subclass(
        "PtxboaFlowCO2_C",
        code="CO2-C",
        name="carbon dioxide (critical phase)",
        template_class_name="PtxboaFlow",
    )
    CO2_G = PtxboaFlow._create_subclass(
        "PtxboaFlowCO2_G",
        code="CO2-G",
        name="carbon dioxide",
        template_class_name="PtxboaFlow",
    )
    DIESEL_L = PtxboaFlow._create_subclass(
        "PtxboaFlowDIESEL_L",
        code="DIESEL-L",
        name="diesel (liquid)",
        template_class_name="PtxboaFlow",
    )
    DRI_S = PtxboaFlow._create_subclass(
        "PtxboaFlowDRI_S",
        code="DRI-S",
        name="Green iron",
        template_class_name="PtxboaFlow",
    )
    EL = PtxboaFlow._create_subclass(
        "PtxboaFlowEL", code="EL", name="electricity", template_class_name="PtxboaFlow"
    )
    H2_G = PtxboaFlow._create_subclass(
        "PtxboaFlowH2_G",
        code="H2-G",
        name="hydrogen (gas)",
        template_class_name="PtxboaFlow",
    )
    H2_L = PtxboaFlow._create_subclass(
        "PtxboaFlowH2_L",
        code="H2-L",
        name="hydrogen (liquid)",
        template_class_name="PtxboaFlow",
    )
    H2O_L = PtxboaFlow._create_subclass(
        "PtxboaFlowH2O_L", code="H2O-L", name="water", template_class_name="PtxboaFlow"
    )
    HEAT = PtxboaFlow._create_subclass(
        "PtxboaFlowHEAT", code="HEAT", name="heat", template_class_name="PtxboaFlow"
    )
    IOP_S = PtxboaFlow._create_subclass(
        "PtxboaFlowIOP_S",
        code="IOP-S",
        name="iron ore pellets",
        template_class_name="PtxboaFlow",
    )
    LOHC_L = PtxboaFlow._create_subclass(
        "PtxboaFlowLOHC_L",
        code="LOHC-L",
        name="hydrogen (LOHC)",
        template_class_name="PtxboaFlow",
    )
    N2_G = PtxboaFlow._create_subclass(
        "PtxboaFlowN2_G", code="N2-G", name="nitrogen", template_class_name="PtxboaFlow"
    )
    NG_G = PtxboaFlow._create_subclass(
        "PtxboaFlowNG_G",
        code="NG-G",
        name="natural gas (gasous)",
        template_class_name="PtxboaFlow",
    )
    NG_L = PtxboaFlow._create_subclass(
        "PtxboaFlowNG_L",
        code="NG-L",
        name="natural gas (liquid)",
        template_class_name="PtxboaFlow",
    )
    NH3_L = PtxboaFlow._create_subclass(
        "PtxboaFlowNH3_L",
        code="NH3-L",
        name="ammonia (liquid)",
        template_class_name="PtxboaFlow",
    )
    STL_S = PtxboaFlow._create_subclass(
        "PtxboaFlowSTL_S",
        code="STL-S",
        name="crude steel",
        template_class_name="PtxboaFlow",
    )


class PtxboaRegions:
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
