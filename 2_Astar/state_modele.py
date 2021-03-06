import copy

class State(object):

    def __init__(self, values, parent=None):
        self.values = values
        self.length = len(self.values)
        self.parent = parent

        #very usefull for oriented search, break nothing for other searches
        self.depth = parent.depth+1 if parent is not None else 0
        # A* _ f = g + h
        self.f = 0 #init so that lt never fails

    def final(self, final_values):
        return self.values == final_values

    def __hash__(self):
        return str(self).__hash__()

    def __str__(self):
        return str(self.values)

    def __eq__(self, other):
        return self.values == other.values
        
    def __lt__(self, other):
        return self.f < other.f

    @staticmethod
    def swap(values, x1, y1, x2, y2):
        # swap two cases in the plate of the puzzle, return a new board array
        new_values = copy.deepcopy(values)
        # python magic this is so good
        new_values [x2][y2], new_values [x1][y1] = values[x1][y1], values[x2][y2] 
        return new_values

    def emptyCase(self) :
        "return the empty case coordinate (i,j) of this state's values (taquin board game)"
        for i in range(self.length) :
            for j in range(self.length) :
                if (self.values[i][j] == 0) :
                    return i,j
        raise Exception("0 not found, problem")

    def inBoardLimits(self, x, y) :
        "return if x,y are in the board limite [0, len]"
        return (x in range(0,self.length)) and (y in range(0, self.length))

    def applicable_operators(self):
        "return all new possible boards after application of legal operators"
        #init array
        ops = []
        #find empty case to be more effective (4 cases to check then)
        xZero, yZero = self.emptyCase()
        #search in square
        for (moveX, moveY) in [(xZero+1, yZero), (xZero-1, yZero), (xZero, yZero+1), (xZero, yZero-1)] :
            #verify we didnt go too far
            if self.inBoardLimits(moveX, moveY) :
                #let the swap give us the new boards generated by the move
                ops.append(State.swap(self.values, xZero, yZero, moveX, moveY))

        return ops

    def apply(self, op) :
        "apply an operation, return the corresponding new state"
        return State(op, self)