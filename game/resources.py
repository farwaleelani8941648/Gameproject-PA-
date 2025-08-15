# game/resources.py

class ResourceManager:
    """
    Tracks player resources throughout the game.
    Handles food, water, coins, and employees.
    """
    def __init__(self):
        self.food = 50
        self.water = 50
        self.coins = 50
        self.employees = 2

    def spend(self, food=0, water=0, coins=0):
        """
        Spend resources. Returns True if successful, False otherwise.
        """
        if self.food >= food and self.water >= water and self.coins >= coins:
            self.food -= food
            self.water -= water
            self.coins -= coins
            return True
        return False

    def earn(self, food=0, water=0, coins=0):
        """
        Earn resources.
        """
        self.food += food
        self.water += water
        self.coins += coins

    def add_employee(self, count=1):
        """
        Add employees.
        """
        self.employees += count

    def remove_employee(self, count=1):
        """
        Remove employees, but never below zero.
        """
        self.employees = max(0, self.employees - count)