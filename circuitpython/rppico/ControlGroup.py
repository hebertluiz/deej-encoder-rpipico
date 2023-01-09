class ControlGroup:
    delta_pos, current_pos, last_pos = (0, 0, 0)

    def __init__(self, encoder, button, enc_multiplier=1):
        self.enc = encoder
        self.enc_multiplier = enc_multiplier
        self.last_pos = self.enc.position
        self.current_pos = None
        self.delta_pos = 0
        self.update()
        
        self.button = button


        self.button.update()

    def update(self):
        self.current_pos = self.enc.position
        self.delta_pos = self.current_pos - self.last_pos
    
    

