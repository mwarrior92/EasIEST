# EasIEST
Easy Internet Experiment Setup Tool
by Marc Anthony Warrior (warrior@u.northwestern.edu)


REDISTRIBUTION --------------------------------------------

- You are free to distribute the download link to this project
- Alternate/changed versions should be posted as BRANCHES to this project (EasIEST)
- If you're doing anything other than the above 2 forms of distribution, please
see https://www.bis.doc.gov/ to make sure you're not doing anything illegal

ABOUT -----------------------------------------------------

EasIEST is all about simplifying the often painful process of deploying and
managing repeatable, large-scale / distributed, Internet measurements.

COMPONENTS ------------------------------------------------
- (1) Measurement Management System (MMS): 
-- should be platform independent
-- should allow for sequences of dependent measurements
-- should allow for experiments to be structured as a sequence MDOs (detailed below)

- (2) Measurement Description Objects (MDOs): 
-- should be platform independent
-- should output in a human-readable format
-- should have extendable APIs

- (3) Platform Layer API (PLA):
-- should interface with arbitrary, platform specific packages / libraries
(Planet Lab, RIPE Atlas, etc.)
-- should be extendable

- (4) Platform Libraries:
-- should provide APIs necessary for the standard platform library
implementations to interface with PLA

- (5) Preset Measurement Plugins (PMPs):
-- should allow for easily repeatable execution of experiments
-- should output human readable descriptions of experiments

System layout:

*---------------------------------------------*
| PMPs______  ______  ______  ______  ______  |
| (5) |Exp.|  |Exp.|  |Exp.|  |Exp.|  |Exp.|  |
|     |A___|  |B___|  |C___|  |D___|  |E___|  |
*---------------------------------------------*
*---------------------------------------------*
| MMS                             * * MDOs    |
| (1)                             * * (2)     |
*---------------------------------------------*
*---------------------------------------------*
| PLA                                         |
| (3)                                         |
*---------------------------------------------*
*---------------------------------------------*
| Libs______  ______  ______  ______  ______  |
| (4) |Lib.|  |Lib.|  |Lib.|  |Lib.|  |Lib.|  |
|     |0___|  |1___|  |2___|  |3___|  |4___|  |
*---------------------------------------------*
