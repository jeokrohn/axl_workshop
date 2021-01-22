# AXL Workshop

Content for a workshop introducing the capabilities of the AXL interface on Cisco Unified CM

To run a Docker container with the prepared demos execute:

`docker run -it --rm --name axl -p 8888:8888 jeokrohn/axl_workshop` 

.. and then point your browser to http://localhost:8888. You will be prompted for a password. The passord is: **axl**

`01 AXL Introduction.py`\
simple examples how to access AXL directly using SOAP envelopes generated for example using [SoapUI](https://www.soapui.org/downloads/soapui.html).

`02 zeep.py`\
Introduction into using `zeep` to access AXL.

`03 mxnumpplan.py`\
Using `zeep` to programmatically provision translation patterns to identify and block mobile numbering ranges in Mexico