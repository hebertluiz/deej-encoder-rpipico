class VirtualPotBank:
    Banks = {}
    MaxValue = 1023
    MinValue = 0
    last, current, delta = ( 0, 0, 0 )
    currentPotBank = 0
    callback = None
    
    def __init__(self,encoder, potNames, toggleDebounced, valueMultiplier=16) -> None:
        self.enc = encoder
        self.button = toggleDebounced
        self.createvirtualPotBanks(potNames)
        self.last = self.enc.position
        self.current = self.enc.position
        self.valueMultiplier = valueMultiplier


    def updateBank(self, bankID):
        
        self.current = self.enc.position
        self.delta = round(int(self.current - self.last) * self.valueMultiplier)
        if self.delta > 0:
            self.virtualPotAdd(bankID, self.delta)
        
        if self.delta < 0: 
            self.virtualPotSub(bankID, self.delta)
        self.resetEncoder()
        return self.Banks[bankID]['Value']

    
    def resetEncoder(self):
        self.delta = 0
        self.last = self.enc.position
    
    def createvirtualPotBanks(self, potNames):
        for pot in range(0, len(potNames)):
            
            
            self.Banks[pot] = {
                'Name': potNames[pot] ,
                'Value':int(
                    self.MaxValue / (8 if potNames[pot] == 'System ' or potNames[pot] == 'Custom1' else 2)
                ) 
            }
            
    def virtualPotAdd(self, bankID, delta):
        if delta + self.Banks[bankID]['Value'] < self.MaxValue :
            self.Banks[bankID]['Value'] = self.Banks[bankID]['Value'] + delta
        else:
            self.Banks[bankID]['Value'] = self.MaxValue
        return self.Banks[bankID]['Value']
    
    def virtualPotSub(self, bankID, delta):
        if delta + self.Banks[bankID]['Value'] > self.MinValue:
            self.Banks[bankID]['Value'] = self.Banks[bankID]['Value'] + delta
        else: 
            self.Banks[bankID]['Value'] = self.MinValue
        return self.Banks[bankID]['Value']

    def returnVirtualPotBanks(self):
        return '|'.join( str(int(value['Value'])) for value in self.Banks.values())

  