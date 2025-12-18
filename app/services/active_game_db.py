import json
import logging
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from ..core.config import settings
from .game_manager import GameState, MoveRecord

logger = logging.getLogger(__name__)


class ActiveGameService:
    def __init__(self):
        self.table_name = "LLM-Duel-ActiveGames"
        self.region = settings.aws_region

        try:
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                self.dynamodb = boto3.resource(
                    "dynamodb",
                    region_name=self.region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
            else:
                self.dynamodb = boto3.resource("dynamodb", region_name=self.region)

            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            logger.error(f"Failed to initialize ActiveGameService: {e}")
            self.table = None

    def save_state(self, state: GameState) -> bool:
        if not self.table:
            return False

        try:
            logger.debug(
                f"[ActiveGameService] Saving state: game_id={state.game_id}, "
                f"turn={state.turn}, moves={len(state.moves)}"
            )
            # Serialize GameState to dict
            item = {
                "game_id": state.game_id,
                "game_type": state.game_type,
                "state": state.state,
                "turn": state.turn,
                "over": state.over,
                "result": state.result,
                "white_model": state.white_model,
                "black_model": state.black_model,
                "white_tokens": state.white_tokens,
                "black_tokens": state.black_tokens,
                "user_id": state.user_id,
                "moves": [
                    {
                        "ply": m.ply,
                        "side": m.side,
                        "move_uci": m.move_uci,
                        "move_san": m.move_san,
                        "model_name": m.model_name,
                        "error": m.error,
                        "from_square": m.from_square,
                        "to_square": m.to_square,
                        "captured_piece": m.captured_piece,
                        "tokens_used": m.tokens_used,
                    }
                    for m in state.moves
                ],
            }

            # DynamoDB doesn't like floats, ensure numbers are Decimal or int?
            # Boto3 handles int/float usually, but let's be safe with JSON serialization if needed.
            # Actually boto3 handles standard types.

            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Error saving game state {state.game_id}: {e}")
            return False

    def load_state(self, game_id: str) -> Optional[GameState]:
        if not self.table:
            return None

        try:
            response = self.table.get_item(Key={"game_id": game_id})
            item = response.get("Item")
            if not item:
                return None

            logger.debug(
                f"[ActiveGameService] Loading state: game_id={game_id}, "
                f"turn={item.get('turn')}, moves={len(item.get('moves', []))}"
            )

            # Deserialize to GameState
            moves = [
                MoveRecord(
                    ply=int(m["ply"]),
                    side=m["side"],
                    move_uci=m["move_uci"],
                    move_san=m.get("move_san"),
                    model_name=m.get("model_name"),
                    error=m.get("error"),
                    from_square=m.get("from_square"),
                    to_square=m.get("to_square"),
                    captured_piece=m.get("captured_piece"),
                    tokens_used=int(m.get("tokens_used", 0)),
                )
                for m in item.get("moves", [])
            ]

            return GameState(
                game_id=item["game_id"],
                game_type=item["game_type"],
                state=item["state"],
                turn=item["turn"],
                over=item["over"],
                result=item.get("result", {}),
                white_model=item.get("white_model"),
                black_model=item.get("black_model"),
                white_tokens=int(item.get("white_tokens", 0)),
                black_tokens=int(item.get("black_tokens", 0)),
                moves=moves,
                user_id=item.get("user_id"),  # Load user_id from DynamoDB
            )
        except ClientError as e:
            logger.error(f"Error loading game state {game_id}: {e}")
            return None


active_game_service = ActiveGameService()
