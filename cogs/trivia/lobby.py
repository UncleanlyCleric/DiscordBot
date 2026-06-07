class TriviaLobby:
    def __init__(self, channel_id: int, host_id: int):
        self.channel_id = channel_id
        self.host_id = host_id

        # core gameplay
        self.players = set()
        self.scores = {}

        # mode control
        self.mode = "classic"  # classic | fibbage

        # state flags
        self.active = False
        self.in_lobby = True

        # classic mode state
        self.current_question = None

        # fibbage state
        self.submissions = {}     # user_id -> fake answer
        self.votes = {}           # user_id -> index of chosen answer
        self.current_choices = [] # mixed answers list

        # flavor systems
        self.host_personality = None
        self.modifier = None

    def add_player(self, user_id: int):
        self.players.add(user_id)
        if user_id not in self.scores:
            self.scores[user_id] = 0

    def reset_round_state(self):
        """Clears per-round data (important for Fibbage + Classic safety)."""
        self.submissions.clear()
        self.votes.clear()
        self.current_choices.clear()
        self.current_question = None