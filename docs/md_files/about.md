# About MARVELO



## The Journey

We started off with the task: "Failover in wireless distributed computing". 
And soon enough we came to our present name **FISSION** - **F**ailover in w**I**rele**SS** d**I**stributed c**O**mputi**N**g. 
Besides matching our initial title in at least some way, **FISSION** describes the opposite of fusion and seemed quite appropriate for out digital splitting of a "core" task.  
Being thrown into this project with two tools, [**MARVELO**](https://github.com/CN-UPB/MARVELO) and [**dispy**](http://dispy.sourceforge.net/), and not too much knowledge of failover, we had some research to do. 

- What is failover?
- What is [**dispy**](http://dispy.sourceforge.net/)?
- What is [**MARVELO**](https://github.com/CN-UPB/MARVELO)?
- How to combine them?!

It turns out that dispy is a framework for "Distributed and Parallel Computing with/for Python". 
Which sounds perfect for our use case at first but reveals some issues when taking another look. 
**dispy** heavily depends on distributing a *single* task onto different nodes with different parameters per node and reporting back to a single entity. 
Communication in between nodes is not intended. In addition **dispy** provides some failover mechanism like heartbeats and fail recovery.  
**MARVELO** on the other hand takes a set of possibly diverse tasks, creates the infrastructure needed for communication in between nodes and computes depending on interim results of different nodes.  
In conclusion booth projects desire to split up compute power onto nodes but do so in two different ways.  
While figuring out the best way of combining them to keep the failover mechanisms of **dispy** while inducing the functionality of **MARVELO** we came across two approaches.  

### The first approach...

...was to keep as much of the current code as possible. 
**MARVELO** has a "Daemon" running on each node of the network to receive and execute commands from a central "Server" (Don't stick to these notions as they change shortly). 
The obvious thing to do is to start the "Daemon" on each reachable node with **dispy** to gain heartbeats and still have all the functionality of **MARVELO**s "Daemons".  
We still had to change some code of the "Server" and while digging into **MARVELO**s code we soon noticed we might want to replace the **MARVELO** code entirely and the second approach was born in parallel.

### The second approach...

...was to get rid of the "Daemons" and provide the whole functionality within a **dispy** job, in other words a single Python function and some dependencies. By doing so, we are able to utilize every node within a network running **dispy**. Which is a huge benefit in booth development and deployment. Setting up nodes becomes easier and while developing your code is centralized and changes can be easily tested as distributing the code is part of the start up process. As a drawback you lose a bit of control over the node as you only spawn jobs, managing them is done by **dispy**.  
Still sounds great, doesn't it? 

Soon enough we had a basic failover mechanism in place using the second approach and with no considerable achievements nor advantages we dropped the first approach and stuck to the second one.  


The core of the problem **FISSION** comes from our predecessor [**MARVELO**](https://github.com/CN-UPB/MARVELO). 
Our goal is to distribute a set of jobs across a set of nodes. 
While doing so, you want your distribution to be optimal in within specific parameters. 
[**MARVELO**](https://github.com/CN-UPB/MARVELO) has an algorithm which needs a lot of computing power to determine a desired distribution and therefore is not suited agile processes like failover mechanisms. This is where **FISSION** kicks in.

## Job Distribution in a failover

If a failover is initiated, some jobs need to be rescheduled onto different nodes.
For this the following procedure is used for each non scheduled job, while the order of the job is random:
1. Looking at all possible nodes in the highest priority GROUP of the job
2. Calculating which nodes fit the best based on given parameter
3. If no node is given or fits, repeat for all other GROUPS of the job
4. Check whether the user wants to calculate the new node himself and getting a node from him
5. If nothing is found abort the current running network

The used parameters for this are:
- `cpu`: free cpu in percentage (close to 100 meaning no load)(average over 3 seconds)
- `swap`: used swap space in percentage (average over 3 seconds)
- `TQ`: Transmit Quality (0 means no connection, 255 means perfect connection)

Since `dispy` is mandatory `cpu` and `swap` are always provided. For having an useful `TQ` value BATMAN-adv needs to be installed otherwise a default value of 255 is used. Furthermore, without BATMAN-adv no routing is provided. See [Install and setup B.A.T.M.A.N-adv](https://git.cs.upb.de/js99/afdwc/-/wikis/fission/Job-Distribution#install-and-setup-batman-adv) on how to install batman and for more information on how BATMAN-adv calculates its `TQ` value visit: [BATMAN_IV](https://www.open-mesh.org/projects/batman-adv/wiki/BATMAN_IV)

Other parameters not used in the default calculation:
- `memory`: free main memory in bytes (average over 3 seconds)
- `disk`: free disk space in bytes (average over 3 seconds)

## Synchronization

A wrapper is build around each job on a node to guarantee synchronization among multiple inputs. 
This wrapper consists of two parts,SQN-Check and Head-Check, which are explained in the following.
The SQN-Check is dealing with the input data of a job and the second part is involved in the output-data of the job.

<img src="synchronization.png"  width="640" height="360">

### SQN-Checker

The SQN-Checker has to check the sequence numbers and headers of the job's incoming data.
In the case of a missing Block a Dummy-Block is build. If the incoming Pipe is ASYNC, the SQN-Checker ignores the Packet completely.

There are two provided modes to generate Dummys. The first is 'zero', where the data from the Packet will be filled with zeros in the right length. The second is 'prev', where the same data from the last Packet will be used. New get_dummy methods can be written in the Pipe. 

The wrapper reads from the input and put the Data, which are represented by Packets, in Queues. 
From these Queues the sequence numbers are checked against a counter, which is increased by 1 every run.
The decisions, which are made in the context of the counter, the SQN and the Reset-Flag for a **new** Packet:
- The **counter starts at 0**, but the SQN of the first Packet is 1. So with the 0 the SQN-Checker knows that he is spawned new. If the counter=0, the counter will be set on the SQN from the next Packet and the Packet will be pushed in the outqueue. So if the first Packet is not getting lost, the counter will be set on 1. 
- Next the SQN_Checker checks **if the Reset-Flag is set**. If it is, the Packet will be pushed to a buffer and a Dummy will be pushed in the outqueue. We have to check all Pipes for the Reset-Flag, before we can push the new Packet in the outqueue, so it is stored and Dummys are pushed until at all Pipes the Reset-Flag was given. Even all Reset-Flags come at the same run, one Dummy per Pipe and per Block_Count will be pushed in the outqueue. 
- Next it is checked if the **SQN is smaller than expected** and the **Reset-Flag is not set**. These Packets will be deleted.
- Next it is checked if the **SQN is higher than expected**. In this case the Packet is pushed in the buffer and a Dummy is pushed in the outqueue.

If the Buffer has a Packet the SQN-Checker checks the following cases:
- First it checks if at all (not ASYNC) Pipes the Reset-Flag were set and if it is in the checking of the first (not ASYNC) Pipe. Then the counter is set on 1, the Packet from the Buffer is pushed in the outqueue and the Reset-Flags will be deleted. 
- If the SQN of the Packet from the Buffer has the expected SQN, the Packet will be pushed in the outqueue.
- If the SQN of the Packet from the Buffer has **not** the expected SQN, a Dummy will be pushed in the outqueue.



### Head-Check

The Head-Check of the wrapper is needed to send the output-data of the current job to the next job.
In order to send these data, there are some steps involved.

First of all, the wrapper reads from the output-pipes of the Job, in order get the data. 
The Head-Check defines data as data without head. 
If the job has decided in the SQN-Checker that he also wants the head, then it also needed to read head from the output-pipes and not only the data.

In case if the head is read from the output-pipe, then the next step is, to check which flags are set by the job. 
There are three flags, corrupted, reset and finished. 
It is not allowed that a connector job, can set a reset flag, only a source job is allowed to set the reset-flag. 
We make distinction between connector jobs, which have inputs and outputs, and source jobs, which have only outputs.

In order to send the data, the calculated output sequence number for connector job from the SQN-Checker is needed, which can be in found in a so called "connection-queue". 
This queue connects SQN-Checker and HEAD-Check.

If a source job is running on the node, then the HEAD-Check has to compute the sequence numbers for the output-blocks. 
The SQN-Checker is not able to compute the sequence numbers because source jobs have no inputs and SQN-Checker is only sitting in front of inputs. 
In case of that, the HEAD-Check is not allowed to use the connection_queue. 
The HEAD-Check also has to add an Head for the output-blocks, where no flags is set in the head.

But if the source job is on his first run, in other words where output-block is produced on the first run, then the reset-flag is set in the output-block automatically. 
In the next runs, the reset flag is not set automatically.

No matter, if there is a source or a connector job running on the node, if we get a command to reset, then on the next run and only in that run, the reset flag is set in the output-block. 
Then also the  sequence number needs to restart to count from 1. 
The command for reset is a timestamp or just a boolean. If in case a timestamp is used the, the reset is set sychronously. The timestamp is just a float-number.

If we have done all the necessary steps for sequence number and head, no matter if there is source or connector job is running on the node, then the output-block needs to be sent to next jobs.

#### Please note:
This is implemented in the module `fission.remote.synchronization` and is instantiated in the module `fission.remote.wrapper`.
To avoid confusion with conventional Packets we refer to Blocks in the documentation. 
The class representing a Block is still called `Packet`.
HEAD Check is called `SendBlock` in the module.










