from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

class GameHandlers:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        self.game_manager.create_game(chat_id)
        await self.game_manager.update_join_message(chat_id, context)

    async def list_players(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        game = self.game_manager.get_game(chat_id)
        
        if not game:
            await update.message.reply_text("No active game!")
            return
            
        if game.game_state != "WAITING":
            await update.message.reply_text("Game already started!")
            return
            
        await self.game_manager.update_join_message(chat_id, context)

    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        game = self.game_manager.get_game(chat_id)
        
        if not game:
            await update.message.reply_text("No active game!")
            return
            
        if game.game_state != "IN_GAME":
            await update.message.reply_text("No active game to end!")
            return
        
        game.game_state = "SCORING"
        await update.message.reply_text(
            "Please enter the final score using the format: /score TeamA TeamB\n"
            "Example: /score 3 2"
        )

    async def handle_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        game = self.game_manager.get_game(chat_id)
        
        if not game:
            await update.message.reply_text("No active game!")
            return
            
        if game.game_state != "SCORING":
            await update.message.reply_text("No game waiting for score!")
            return
        
        try:
            if not context.args or len(context.args) != 2:
                raise ValueError
                
            score_a, score_b = map(int, context.args)
            if score_a < 0 or score_b < 0:
                raise ValueError
                
        except (ValueError, IndexError):
            await update.message.reply_text(
                "Invalid score format.\n"
                "Please use: /score TeamA TeamB\n"
                "Example: /score 3 2"
            )
            return

        game.score = {"Team A": score_a, "Team B": score_b}
        
        # Announce the final score before MVP voting
        await update.message.reply_text(
            f"Final Score:\n"
            f"Team A: {score_a}\n"
            f"Team B: {score_b}\n"
        )
        
        # Start MVP voting
        await self.start_mvp_voting(update, context)

    async def start_mvp_voting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        game = self.game_manager.get_game(chat_id)
        
        if not game:
            await update.message.reply_text("No active game!")
            return
        
        # Change state to voting
        game.game_state = "VOTING"
        game.mvp_votes = {}  # Reset/initialize MVP votes
        
        # Create voting keyboard with full names
        keyboard = []
        for player in game.players:
            # Handle cases where last_name might be None
            player_name = (f"{player.first_name} {player.last_name}" 
                        if player.last_name 
                        else player.first_name)
            button = InlineKeyboardButton(
                player_name,
                callback_data=f"vote_{player.id}"
            )
            keyboard.append([button])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏆 Vote for MVP! 🏆\n"
            "Choose the most valuable player:",
            reply_markup=reply_markup
        )
