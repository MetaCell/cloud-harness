# Custom JupyterHub

This Helm chart is forked from the main JupyterHub helm chart and adapted to CloudHarness path structure.

The main personalizations happen in the file `jupyterhub_config.py` in order to implement the following 
dynamic behaviours like:
 - Use a different image based on current path/parameter
 - Mount custom volumes