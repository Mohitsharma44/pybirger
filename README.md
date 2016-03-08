# pybirger
Python wrapper for Birger Adapter: #RD-EF1-EV2-EV1 controlling Cannon EF 232 mounted on
Emergent HS 12000C Camera*

The wrapper will help control almost all the parameters of the lens
that is mentioned in the cannon ef232's reference manual. 

Cannon EF 232 Birger Adapter Reference Library can be found here:
http://www.birger.com/pdf/ef232_user_manual.pdf


Birger adapter is controlled using serial communication by default
however for my application, I had installed a [Lantronix UDS 1100](http://www.lantronix.com/products/uds1100-uds1100-poe/)
with the [DB9 null modem Male-to-Male connector](http://www.amazon.com/CablesOnline-Slimline-Transfer-Adapter-AD-N05M-2/dp/B00HGJ7JMU/ref=sr_1_6?s=pc&ie=UTF8&qid=1454600905&sr=1-6&keywords=null+modem+adapter+db9+male+to+male) to be able to control everything over the ethernet

For help regarding configuration of UDS 1100, refer the manual [here](http://www.lantronix.com/wp-content/uploads/pdf/UDS1100_UG.pdf)

> *The camera shouldn't matter
