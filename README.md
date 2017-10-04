# EASIEST
Expressive And Simple Internet Experiment Setup Tool
by Marc Anthony Warrior (warrior@u.northwestern.edu)


REDISTRIBUTION --------------------------------------------

- You are free to distribute the download link to this project  
- Alternate/changed versions should be posted as BRANCHES to this project (EasIEST)  
- If you're doing anything other than the above 2 forms of distribution, please  
see https://www.bis.doc.gov/ to make sure you're not doing anything illegal  

ABOUT -----------------------------------------------------

EasIEST is all about simplifying the often painful process of deploying and
managing repeatable, large-scale / distributed, Internet measurements.

GOALS -----------------------------------------------------
1) create an overlay system that allows for experiments to be placed on top and platform management to happen underneath
2) structure experiment management such that details are easy to parse/recover
3) structure experiment management such that written experiments can be repeated easily
4) structure overlay to allow for cross-platform (RIPE Atlas, Planet Lab, etc) experiments
5) leverage multi-platform access to choose optimal client pools for experiments
6) structure code to allow for quick and easy extensibility (in other words, minor, experiment-specific needs should not
require any changes to the tool)

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

