import { AnimateSharedLayout } from "framer-motion";
import TableStack from "./TableStack/TableStack.jsx";
import PlayerStack from "./PlayerStack/PlayerStack.jsx";
import { useEffect, useState } from "react";
import LeftStack from "./LeftStack/LeftStack.jsx";
import RightStack from "./RightStack/RightStack.jsx";
import TopStack from "./TopStack/TopStack.jsx";
import DrawingStack from "./DrawingStack/DrawingStack.jsx";
import { useDispatch, useSelector } from "../../utils/hooks";
import {
  moveCard,
  movePlayer,
  stopGame,
} from "../../stores/features/gameSlice";
import Scoreboard from "./Scoreboard/Scoreboard.jsx";
import { Player } from "../../utils/interfaces.js";
import API from "../../api/API";
import { Navigate, } from "react-router";
import GameAudio from "../../utils/audio.js";

export default function Game() {
  const dispatch = useDispatch();
  const [finished, setFinished] = useState(false)
  const [playersOrder, setPlayersOrder] = useState<Player[]>([]);
  const inGame = useSelector(state => state.game.inGame)
  const { players, playerId } = useSelector((state) => ({
    players: state.game.players,
    playerId: state.game.playerId,
  }));
  const spectating = Array.isArray(players) && playerId && !players.some((p: any) => p && p.id === playerId);


  useEffect(() => {
    const timeoutReady = setTimeout(() => {
      API.emitReady()
    }, 2000)
    API.onMove(({ card, draw, cardsToDraw, nxtPlayer }) => {

      dispatch(
        moveCard({
          nextPlayer: nxtPlayer,
          card,
          draw,
          cardsToDraw,
        })
      );
      if (draw) {
        GameAudio.playAudio('draw', draw);
      } else GameAudio.playAudio('play')
      setTimeout(() => dispatch(movePlayer()), 500);
    })

    API.onFinishGame((players: Player[]) => {
      setFinished(true);
      setPlayersOrder(players);
    })

    return () => {
      API.leaveServer();
      dispatch(stopGame());
      clearTimeout(timeoutReady)
    }
  }, [dispatch]);


  if (!inGame) return <Navigate replace to="/main-menu" />;

  return (
    <div>
      <AnimateSharedLayout>
        <TableStack />
        <TopStack />
        <LeftStack />
        <RightStack />
        <PlayerStack />
        <DrawingStack />
      </AnimateSharedLayout>

      {spectating && (
        <div
          style={{
            position: 'fixed',
            top: 12,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0,0,0,0.6)',
            color: 'white',
            padding: '6px 12px',
            borderRadius: 8,
            fontSize: 14,
            zIndex: 1000,
            pointerEvents: 'none',
          }}
          title="You are spectating an all-LLM Arena match"
        >
          Arena (Spectating)
        </div>
      )}

      {finished && <Scoreboard players={playersOrder} />}
    </div>
  );
}
