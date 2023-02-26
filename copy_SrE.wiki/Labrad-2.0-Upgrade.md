```python
In [9]: r = cxn.registry

In [10]: r.dir()
Out[10]: (['Nodes', 'Servers'], [])

In [11]: r.cd('Nodes')
Out[11]: ['', 'Nodes']

In [12]: r.dir()
Out[12]: 
(['__default__', 'yebigbird', 'yecookiemonster', 'yecountvoncount', 'yeelmo'],
 [])

In [13]: r.cd('yeelmo')
Out[13]: ['', 'Nodes', 'yeelmo']

In [14]: r.dir
Out[14]: 
LabRAD Setting: "Registry" >> "dir" (ID=1)

Returns lists of the subdirs and keys in the current directory.

Accepts:
    _

Returns:
    (*s*s)

 

In [15]: r.dir()
Out[15]: ([], ['autostart', 'directories', 'extensions'])

In [16]: r.get('directories')
Out[16]: ['/home/srgang/SrE/labrad_tools/']

In [17]: r.set('directories', ['/home/srgang/labrad_tools'])
```