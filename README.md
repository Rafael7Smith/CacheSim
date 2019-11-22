# CacheSim
Python.  Simulates a single level cache given a file of operations and addresses.  Runtime is excessive for included test case (avg 100 seconds)

Test file was 335MB of randomized operations and addresses in the following format:

<op> <address>

ex:
W 0x7fff6c5b7b20
W 0x7fff6c5b7b18
W 0x7fff6c5b7b10
W 0x7fff6c5b7b08
W 0x7fff6c5b7af8
W 0x7fff6c5b7af0
W 0x7fff6c5b7ae8
W 0x7fff6c5b7ae0
W 0x7fff6c5b7ad8
R 0x7f995cf0ffc8
R 0x7f995d27b760
R 0x7f995d27b740
R 0x7f995cf10230

Program takes serveral arguments
<size of cache in Bytes> <Associativity of Cache> <Replacement policy: 0 = LRU, 1 = FIFO> <Write policy: 0 = Write Through, 1 = Write Back> <Trace File>
