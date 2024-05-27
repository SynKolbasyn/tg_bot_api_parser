class Type:
    def __init__(self, name: str, tg_type: str, optional: bool):
        """
        Initializes the Type class

        :param name: Type name
        :param tg_type: Telegram bot api type of type
        :param optional: Is the type optional
        """

        self.name = name
        self.tg_type = tg_type
        self.optional = optional
