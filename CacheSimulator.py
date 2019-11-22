import sys
import math
import time

#global vars
DEBUG = False
bit_array = [] #index, offset, tag, num_sets
cache_Array = [[]]
cache_MetaData = [[[]]]  #for [index][i] = [0,0] first number will be for replace, 2nd for valid
cache_Assoc = 0
memory_writes = 0
    
#cache index offset tag
def CacheIOT(trace_address):
    global DEBUG
    global bit_array

    num_sets = bit_array[3]
    #split hex address from trace_address'
    hex_address = trace_address[2:]
    
    int_address = int(hex_address, 16)
    index = (int_address / 64) % num_sets
    tag = int_address / 64              #gives tag + offset

    return int(index), int(tag)

# returns the assoc # of the Least recently used spot for given index
def FindLRUCache(index, tag):
    global cache_Array, cache_MetaData, cache_Assoc

    LRU_assoc = 0
    LRU_rank = -1
    for i in range(cache_Assoc):
        if(cache_MetaData[index][i][0] > LRU_rank):
            LRU_assoc = i
            LRU_rank = cache_MetaData[index][i][0]
    return LRU_assoc

# returns the assoc # of the first address for given index
def FindFIFOCache(index, tag):
    global cache_Array, cache_MetaData, cache_Assoc
    ret_fifo = 0

    for i in range(cache_Assoc):
        if(cache_MetaData[index][i][0] == 0):
            ret_fifo = i
    return ret_fifo

#will go through and update FIFO rankings, setting tag location to max
def UpdateFIFO(index, tag):
    global cache_Array,cache_MetaData, cache_Assoc
    for i in range(cache_Assoc):
        if(cache_Array[index][i] == tag):
            cache_MetaData[index][i][0] = cache_Assoc
        else:
            cache_MetaData[index][i][0] = cache_MetaData[index][i][0] - 1
    return

#will go through and update # of instruction since last call for each address within index
def UpdateLRU(index, tag):
    global cache_Array, cache_MetaData, cache_Assoc

    for i in range(cache_Assoc):
        if(cache_Array[index][i] == tag):
            cache_MetaData[index][i][0] = 0
        else:
            cache_MetaData[index][i][0] = cache_MetaData[index][i][0] + 1

    return

#for writeBack policy, will mark metadata as dirty for given tag
def UpdateWB(index, tag):
    global cache_Array, cache_MetaData, cache_Assoc

    for i in range(cache_Assoc):
        if(cache_Array[index][i] == tag):
            cache_MetaData[index][i][1] = 1
            break

    return

#takes address and adds information to cache_Array and cache_Metadata
def WriteCache(index, tag, repl_policy, write_policy):
    global cache_Array, cache_MetaData, cache_Assoc
    global memory_writes
    num_writes = 0
    write_success = False

    #check for empty spots
    for i in range(cache_Assoc):
        if(cache_Array[index][i] == 0):
            cache_Array[index][i] = tag
            if(repl_policy == 1): #FIFO number
                cache_MetaData[index][i][0] = i
            else: #LRU, 0 instructions since last use
                UpdateLRU(index, tag)
            write_success = True
            break

    #if cache is full
    if(write_success == False):
        if(repl_policy == 1): #FIFO
            #find the who has the 0, eg first in
            min_assoc = FindFIFOCache(index, tag)
            cache_Array[index][min_assoc] = tag
            UpdateFIFO(index, tag)
            #if WriteBack (1), and block marked dirty (1), write to cache
            if((write_policy == 1) and (cache_MetaData[index][min_assoc][1] == 1)):
                memory_writes = memory_writes + 1
                cache_MetaData[index][min_assoc][1] = 0 #reset block
            
        else: #LRU
            LRU_assoc = FindLRUCache(index, tag)
            #assign tag to location
            cache_Array[index][LRU_assoc] = tag
            UpdateLRU(index, tag)
            if((write_policy == 1) and (cache_MetaData[index][LRU_assoc][1] == 1)):
                memory_writes = memory_writes + 1
                cache_MetaData[index][LRU_assoc][1] = 0

    return num_writes

#returns boolean on address checked
def Checkcache(index, tag):
    global cache_Array, cache_Assoc
    for i in range(cache_Assoc):
        if(tag == cache_Array[index][i]):
            return True

    return False

def Cachetrace(trace_file_name, repl_policy, write_policy):
    global DEBUG
    global cache_Array,cache_MetaData, cache_Assoc, memory_writes

    #likely not neded, paranoid that uninitialized values might not be 0
    retval = 0
    write_ops = 0
    read_ops = 0
    num_miss = 0
    num_hits = 0
    num_reads = 0
    memory_writes = 0


    #primary file loop
    with open(trace_file_name) as trace_file:
        for operation in trace_file:
            op_index, op_tag = CacheIOT(operation)

            if(operation[0] == 'R'):
                read_ops = read_ops + 1
                if(Checkcache(op_index, op_tag)):
                    num_hits = num_hits + 1
                else:
                    num_miss = num_miss + 1
                    WriteCache(op_index, op_tag, repl_policy, write_policy)
                    num_reads = num_reads + 1 #everytime we read and miss cache, we must read from memory
                if(repl_policy == 0): #LRU replacement policy
                        UpdateLRU(op_index,op_tag)
                pass

            
            if(operation[0] == 'W'):
                write_ops = write_ops + 1
                if(Checkcache(op_index, op_tag)):
                    num_hits = num_hits + 1
                    if(write_policy == 1): #if address is in cache, and WriteBack Policy, mark address as dirty
                        UpdateWB(op_index, op_tag)
                    else: #write through policy, always write
                        memory_writes = memory_writes + 1
                else:
                    num_miss = num_miss + 1
                    num_reads = num_reads + 1
                    WriteCache(op_index, op_tag, repl_policy, write_policy)
                    if(write_policy == 1): #if address is in cache, and WriteBack Policy, mark address as dirty
                        UpdateWB(op_index, op_tag)
                    else: #write through policy, always write
                        memory_writes = memory_writes + 1
                if(repl_policy == 0): #LRU replacement policy
                        UpdateLRU(op_index, op_tag)
            if(operation[0] == ' '):
                pass

    print("{:.6f}".format(float(num_miss)/(read_ops + write_ops)))
    print(memory_writes)
    print(num_reads)

    return 

def main():
    global DEBUG
    global cache_Array, cache_MetaData, bit_array, cache_Assoc

    Size = int(sys.argv[1]) #size in bytes
    cache_Assoc = int(sys.argv[2])
    cache_Repla = int(sys.argv[3]) #0 = LRU, 1 = FIFO
    cache_Write = int(sys.argv[4]) #0 = write Through, 1 = write back
    trace_file_name = str(sys.argv[5])
  
    #number of sets =  CacheSize / (blockSize * Assco)
    cache_Block = 64
    num_sets = int(Size / (cache_Block * cache_Assoc))
    num_index = math.log(num_sets, 2)
    num_offset = math.log(cache_Block,2)
    num_tag = 64 - num_index - num_offset

    print("Index: ", num_sets)
    bit_array = [num_index,num_offset,num_tag, num_sets]
    
    #create cache Arrays and metadata arrays
    cache_Array = [[0 for x in range(cache_Assoc)] for y in range(int(num_sets))]
    cache_MetaData = [[[0,0] for x in range(cache_Assoc)] for y in range(int(num_sets))]
    start = time.time()
    Cachetrace(trace_file_name, cache_Repla, cache_Write)
    end = time.time()
    print("Program runtime: {}".format(end - start))
    return

main()
