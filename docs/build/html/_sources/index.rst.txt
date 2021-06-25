MARVELO
=======

This project is a Python based solution for distributing a set of dependent tasks onto multiple devices.
It is having a failover mechanism in place to prevent outage of your cluster, called **Fission**, which uses **dispy** (http://dispy.sourceforge.net/)s heartbeat, monitoring and job cluster functionality.
If you have not set up a cluster yet, **MARVELO** may still be useful for you since it provides a **simulator** to run a "cluster" on your local machine.

**MARVELO** is still in development


Your First Steps
----------------
We recommennd to go through the examples or watch the [video]() *will come soon* to see if MARVELO suits your concepts and expectations. After that, install and work through **How to use MARVELO**. Then you should be able do understand the implementation of the examples and to implement your own simple ones. Look at **develop your own Network** for deeper insights.


Structure
---------
On page **Getting Started** you will find the installation guide and an overview about MARVELO's terminaology.

**How to use MARVELO** goes through a simple example step by step and explains the necessary commands. After working through that page, you should be able to implement your own simple networks.

**Develop your own Network** explains the usage of MARVLEO in more detail.

**Example Networks** shows some simple examples, a step-by-step tutorial on how to implement a complex network and some acoustic signal processing applications. 

On the **Documentation** page, you will find the source code itself, and how to use or inherit from existing jobs, pipes, etc. 

If you are interested in the background of MARVELO, look at **About MARVELO**.


.. toctree::
   :maxdepth: 2

   md_files/getting_started
   md_files/usage
   development
   example_networks
   documentation
   md_files/about
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

