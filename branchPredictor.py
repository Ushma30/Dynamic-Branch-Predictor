#!/usr/bin/python3
'''
##############################################################################################
University of North Carolina Charlotte
Course : Computer Architecture by Dr. Hamed Tabkhi

Branch Predictor Perceptron
  
(^_^)

Date : December 5, 2018
##############################################################################################
'''
import sys
import getopt
verbosity = 0
'''
Predict(fileAddress)
    Reads the trace file passed as argument to this fucntion
    Based on the selected predictor get the correctOutcome
    @return [NoOfLines]
    
'''
def Predict(fileAddress):
    NoOfLines = 0
    global corretOutcome
    with open(fileAddress) as f:
        for lines in f:        
            NoOfLines = NoOfLines + 1
            #if its a SPEC trace file then Extract data of branch address and branchStatus 
            if FileFormat == 'trace':
                dataInLine = lines.split(' ')
                branchAddress = int(dataInLine[0], 10)
                branchStatus = dataInLine[1].rstrip('\n')
            #if its a Pintool trace file then Extract data of branch address and branchStatus 
            elif FileFormat == 'out':
                dataInLine = lines.split('\t')
                branchAddress = int(dataInLine[7].split(' ')[14], 16)
                branchStatus = dataInLine[1]
                if branchStatus == '1':
                    branchStatus = 'T'
                else:
                    branchStatus = 'N'
            if PredictorType == 1:
                if branchStatus == OneLevelBranchPredictor(branchAddress,branchStatus):
                    corretOutcome = corretOutcome + 1
            elif PredictorType == 2:
                if branchStatus == TwoLevelGlobalBranchPredictor(branchAddress,branchStatus):
                    corretOutcome = corretOutcome + 1
            elif PredictorType == 3:            
                if branchStatus == Gshare(branchAddress,branchStatus):  
                    corretOutcome = corretOutcome + 1
            elif PredictorType == 4:            
                if branchStatus == TwoLevelLocalBranchPredictor(branchAddress,branchStatus):
                    corretOutcome = corretOutcome + 1
            elif PredictorType == 5: 
                if branchStatus == TournamentPredictor(branchAddress,branchStatus):
                    corretOutcome = corretOutcome + 1
            elif PredictorType == 6:
                if branchStatus == perceptronPredictor(branchAddress,branchStatus):
                    corretOutcome = corretOutcome + 1
        print("Total Branches = ",NoOfLines)
    return NoOfLines

'''
returnStatus(status)
    Returns N or T based on the predicator value
    @return [Taken or not Taken]
'''
def returnStatus(status):
    #shift the status by the no of bits in the predicator to get the last bit 
    if (status >> (PredictionBits - 1)) == 0:
        return 'N'
    else:
        return 'T'
'''
OneLevelBranchPredictor(branch,status)
    The one level Branch Predictor returns if the prediction is ture or false
    @return predictedStatus
''' 
def OneLevelBranchPredictor(branch,status):
    #get index from the branch and reduce it to PHT_size
    index = (branch>>StaticBitShift) % PHT_Size
    #get the prediction from the PHT
    predictedStatus = returnStatus(PatternHistoryTable[index])
    #Increment the Predicator counter based on Taken or Not taken
    if status == 'N':
        if PatternHistoryTable[index] > PredictorMin:
            PatternHistoryTable[index] = PatternHistoryTable[index] - 1  
    else:
        if PatternHistoryTable[index] < PredictorMax:
            PatternHistoryTable[index] = PatternHistoryTable[index] + 1
    return predictedStatus

'''
TwoLevelGlobalBranchPredictor(branch,status)
    @return predictedStatus
'''                   
def TwoLevelGlobalBranchPredictor(branch,status):
    global GlobalHistoryRegistor
    #Limit the predicator to the size of PHT
    GlobalHistoryRegistor = GlobalHistoryRegistor % PHT_Size
    #get the prediction from the PHT
    predictedStatus = returnStatus(PatternHistoryTable[GlobalHistoryRegistor])
    if status == 'N':
        if PatternHistoryTable[GlobalHistoryRegistor] > PredictorMin:
            PatternHistoryTable[GlobalHistoryRegistor] = PatternHistoryTable[GlobalHistoryRegistor] - 1 
        GlobalHistoryRegistor = ( (GlobalHistoryRegistor << 1) | 0 ) % PHT_Size
    else:
        if PatternHistoryTable[GlobalHistoryRegistor] < PredictorMax:
            PatternHistoryTable[GlobalHistoryRegistor] = PatternHistoryTable[GlobalHistoryRegistor] + 1
        GlobalHistoryRegistor = ( (GlobalHistoryRegistor << 1) | 1 ) % PHT_Size
    return predictedStatus

'''
Gshare(branch,status)
    @return predictedStatus
'''    
def Gshare(branch,status):
    global GlobalHistoryRegistor_Gshare
    ImpBitsInBranch = branch >> StaticBitShift
    GlobalHistoryRegistor_Gshare = GlobalHistoryRegistor_Gshare % PHT_Size
    Index = GlobalHistoryRegistor_Gshare ^ ImpBitsInBranch
    Index = Index % PHT_Size
    predictedStatus = returnStatus(PatternHistoryTable[Index])
    if status == 'N':
        if PatternHistoryTable[Index] > PredictorMin:
            PatternHistoryTable[Index] = PatternHistoryTable[Index] - 1 
        GlobalHistoryRegistor_Gshare = ((GlobalHistoryRegistor_Gshare << 1) | 0)%PHT_Size
    else:       
        if PatternHistoryTable[Index] < PredictorMax:
            PatternHistoryTable[Index] = PatternHistoryTable[Index] + 1
        GlobalHistoryRegistor_Gshare = ((GlobalHistoryRegistor_Gshare << 1) | 1)%PHT_Size
    return predictedStatus

'''
TwoLevelLocalBranchPredictor(branch,status)
    @return predictedStatus
'''     
def TwoLevelLocalBranchPredictor(branch,status):
    global GlobalHistoryRegistor
    ImpBitsInBranch = branch >> StaticBitShift
    LocalIndex = ImpBitsInBranch % LHR_Size
    PHT_Index = LocalHistory[LocalIndex]
    predictedStatus = returnStatus(PatternHistoryTable[PHT_Index])
    if status == 'N':
        if PatternHistoryTable[PHT_Index] > PredictorMin:
            PatternHistoryTable[PHT_Index] = PatternHistoryTable[PHT_Index] - 1 
        LocalHistory[LocalIndex] = (LocalHistory[LocalIndex] << 1) | 0
        LocalHistory[LocalIndex] = LocalHistory[LocalIndex] % PHT_Size
    else:
        if PatternHistoryTable[PHT_Index] < PredictorMax:
            PatternHistoryTable[PHT_Index] = PatternHistoryTable[PHT_Index] + 1
        LocalHistory[LocalIndex] = (LocalHistory[LocalIndex] << 1) | 1
        LocalHistory[LocalIndex] = LocalHistory[LocalIndex] % PHT_Size
    return predictedStatus

'''
TournamentPredictor(branch,status)
    @return predictedStatus
'''  
def TournamentPredictor(branch,status):
    global GlobalHistoryRegistor_Gshare
    #Two Level Local Prediction
    TLBPrediction = OneLevelBranchPredictor(branch,status)
    #Gshare
    global GlobalHistoryRegistor_Gshare
    ImpBitsInBranch = branch >> StaticBitShift
    GlobalHistoryRegistor_Gshare = GlobalHistoryRegistor_Gshare % PHT_Size_Tournament
    Index = GlobalHistoryRegistor_Gshare ^ ImpBitsInBranch
    Index = Index % PHT_Size_Tournament
    GlobalHistoryRegistor_Gshare = Index
    GsharePrediction = returnStatus(PatternHistoryTable_Tournament[Index])
    if status == 'N':
        if PatternHistoryTable_Tournament[Index] > PredictorMin:
            PatternHistoryTable_Tournament[Index] = PatternHistoryTable_Tournament[Index] - 1 
        GlobalHistoryRegistor_Gshare = ((GlobalHistoryRegistor_Gshare << 1) | 0)%PHT_Size_Tournament
    else:       
        if PatternHistoryTable_Tournament[Index] < PredictorMax:
            PatternHistoryTable_Tournament[Index] = PatternHistoryTable_Tournament[Index] + 1
        GlobalHistoryRegistor_Gshare = ((GlobalHistoryRegistor_Gshare << 1) | 1)%PHT_Size_Tournament
    #Choice predictor
    if (PredictorSelector[GlobalHistoryRegistor_Gshare] >> (PredictorSelctorBits -1)) == 1:
        FinalPrediction = GsharePrediction
    else:
        FinalPrediction = TLBPrediction
    #INcrement the counter in the predicor selector if the prediction of Gshare is true
    if status == GsharePrediction == TLBPrediction:
        pass
    elif status == GsharePrediction:
        if PredictorSelector[GlobalHistoryRegistor_Gshare] < (2 ** PredictorSelctorBits) - 1:
            PredictorSelector[GlobalHistoryRegistor_Gshare] = PredictorSelector[GlobalHistoryRegistor_Gshare] + 1
    elif status == TLBPrediction:
        if PredictorSelector[GlobalHistoryRegistor_Gshare] > 0:
            PredictorSelector[GlobalHistoryRegistor_Gshare] = PredictorSelector[GlobalHistoryRegistor_Gshare] - 1

    return FinalPrediction

def perceptronPredictor(branch,status):
    global GlobalHistoryRegistor
    y = 1
    #shift the branch data by 2 bits 
    ImpBitsInBranch = branch >> StaticBitShift
    #Get the index from the branch by taking modulas
    LocalIndex = ImpBitsInBranch % PHT_Size
    #Convert the GHR to GHR bits to convert 0 to -1
    GHR_Bitwise = [int(x) for x in '{:010b}'.format(GlobalHistoryRegistor)]
    #Convert the GHR bits from 1010 to 1,-1,1,-1
    for i in range(len(GHR_Bitwise)):
        if GHR_Bitwise[i] == 0:
            GHR_Bitwise[i] = -1
    #get the perceptron weights
    perceptronWeights = PerceptronTable[LocalIndex]
    #Compute the y using weights and GHR
    for i in range(len(perceptronWeights)):
        y = y + perceptronWeights[i]*GHR_Bitwise[i]
    #Get the prediction from the calculated y 
    if y > 0:
        #print("Prediction = Taken ")
        predictedStatus = 'T'
    else:
        #print("Prediction = Not Taken ")
        predictedStatus = 'N'
    #get t value from actual status of branch
    if status == 'T':
        GlobalHistoryRegistor = ((GlobalHistoryRegistor << 1) | 1)%PHT_Size
        t = 1
    else:
        t = -1
        GlobalHistoryRegistor = ((GlobalHistoryRegistor << 1) | 0)%PHT_Size
    #update the weights if prediction is not equal to status
    if status != predictedStatus:
        for i in range(len(perceptronWeights)):
            perceptronWeights[i] = perceptronWeights[i] + t*GHR_Bitwise[i]
    #Update the Perceptron Table with weights 
    PerceptronTable[LocalIndex] = perceptronWeights
    return predictedStatus
    
'''
usage()
    The help and information regardind the simulator
''' 
def usage():
    print ("""Usage: [-hv] [-f file Path] [-P PHT Size ] [-L LHR Size] [ -T Predicator Type ] [-b Predicator Counter Bits] 

 ************* Branch Predictor *************
        
    -h               This help
    -v               Verbose
    -f               FIle path
    -P               PHT Size
    -L               LHR Size
    -T               Predicator Type
                         1 -> One Level Branch Predictor
                         2 -> Two Level Global Branch Predictor
                         3 -> Gshare Branch Predictor
                         4 -> Two Level Local Branch Predictor
                         5 -> Tournament Predictor
                         6 -> Perceptron Predictor
    -b               Predicator Counter Bits

    Eg: For Predictor 1-4 
        $ python3 branchPredictor.py -f branch-trace-gcc.trace -P 1024 -L 128 -T 1 -b 2
    Eg: For 5 (Tournament ) Predictor
        $ python3 branchPredictor.py -f branch-trace-gcc.trace -P 1024 -L 128 -C 1024 -T 5 -b 3
       
    """)
corretOutcome =0
if __name__ =='__main__':
    #Get the Cache configuratiimon from the arguments
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hv:f:b:P:G:L:T:C:")
    except getopt.GetoptError as err:
        print (str(err))
        usage()
        exit()
    for opt,arg in opts:
        if opt in ['-h']:
            usage()
            exit()
        elif opt in ['-f']:
            filePath = arg
        elif opt in ['-P']:
            PHT_Size = int(arg)
        elif opt in ['-G']:
            GHR_Size = int(arg)
        elif opt in ['-b']:
            PredictionBits = int(arg)
        elif opt in ['-L']:
            LHR_Size = int(arg)
        elif opt in ['-C']:
            PHT_Size_Tournament = int(arg)
        elif opt in ['-T']:
            PredictorType = int(arg)
        elif opt in ['-v']:
            verbosity = 1
    #get the file path and Display whether its a .trace(SPEC2000 File) file or 
    #.out(File generated by pintool) file  
    FileFormat = filePath.split('.')[1]

    if FileFormat == 'trace':
        print("It's a .Trace File")
    elif FileFormat == 'out':
        print("It's a .out File")
    else:
        print("Wrong File <_>")
        exit(0)
    #Print which predictor we have selected
    if PredictorType == 1:
        print("OneLevelBranchPredictor")
    elif PredictorType == 2:
        print("TwoLevelGlobalBranchPredictor")
    elif PredictorType == 3:            
        print("Gshare")
    elif PredictorType == 4:            
        print("TwoLevelLocalBranchPredictor")
    elif PredictorType == 5:            
        print("TournamentPredictor")
    elif PredictorType == 6:            
        print("Perceptron Predictor")
    #Remove the redundent bits from the PC
    StaticBitShift = 2
    #Get the Min Max limit of the Predicator from bits
    PredictorMin = 0
    PredictorMax = (2 ** PredictionBits) - 1
    #Initilize the PHT table with Size 0 
    PatternHistoryTable = [0]*PHT_Size
    #perceptron Table 
    PerceptronTable = [([0]*10) for row in range(PHT_Size)]
    #Set the Size for PHT of Gshare and the Predicator chooser for Tournament Predictor
    PatternHistoryTable_Tournament = [0]*PHT_Size_Tournament
    PredictorSelector = [0]*PHT_Size_Tournament
    GlobalHistoryRegistor_Gshare = 0
    PredictorSelctorBits = 2

    #Set the local History Size 
    LocalHistory = [0]*LHR_Size
    #Initilize the GHR to 0
    GlobalHistoryRegistor = 0
    
    
    #Read the file passed in the argument and seperate instructions, data and unified 
    TotalInstructions = Predict(filePath)
    #print the no of correct outcomes 
    print("Correct Prediction = ",corretOutcome)
    #print the Prediction Percentage
    print("Prediction % = ",round((corretOutcome/TotalInstructions)*100,3),"%")
    #print(PerceptronTable)
    print("---------------------------Finish-------------------------------")

######################################################################################################
