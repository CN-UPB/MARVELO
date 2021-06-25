# Create a new Project

To start a new **MARVELO** project just run:

```bash
fission_admin.py <my-project> startproject
```

This will result in the following structure:

```
<my-project>/
├── manage.py
└── shared
    ├── __init__.py
    ├── jobs
    │   ├── __init__.py
    │   └── jobs.py
    ├── nodes
    │   ├── __init__.py
    │   └── nodes.py
    ├── pipes
    │   ├── __init__.py
    │   └── pipes.py
    └── source
```

By default a `shared` network is started. 
It contains no `config.py` file and there for can't be directly executed.  
It's purpose is to hold jobs, nodes, pipes and files you may want to use in multiple networks within you project.

Next head into ```<my-project>``` and start a network:

```bash
cd <my-project>
python3 manage.py <my-network> startnetwork
```

The folder structure changes to:

```
<my-project>/
├── manage.py
├── shared
│   ├── __init__.py
│   ├── jobs
│   │   ├── __init__.py
│   │   └── jobs.py
│   ├── nodes
│   │   ├── __init__.py
│   │   └── nodes.py
│   ├── pipes
│   │   ├── __init__.py
│   │   └── pipes.py
│   └── source
└── <my-network>
    ├── config.py
    ├── __init__.py
    ├── jobs
    │   ├── __init__.py
    │   └── jobs.py
    ├── nodes
    │   ├── __init__.py
    │   └── nodes.py
    ├── pipes
    │   ├── __init__.py
    │   └── pipes.py
    └── source
```

Notice how our newly created network provides a `config.py` file, meaning we can actually run it.

We'll return to the config later, first a quick explanation of what's what:

- ```config.py``` is the part of your network where you define a few general things, but also how and with what pipes your jobs are connected.

- ```jobs``` is a directory / python module where you are meant to define your jobs in.

- ```nodes``` is a directory / python module where you are meant to define your nodes in.

- ```pipes``` is a directory / python module where you are meant to define, you guessed it, your pipes in.

- ```source``` is a directory where you are meant to put your job's dependencies like executables or in general files you job depends on.




