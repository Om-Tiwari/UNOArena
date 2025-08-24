import styled from "styled-components";
import { useSelector } from "../../../utils/hooks";
import CardsRow from "../CardsRow/CardsRow";

const Root = styled.div`
  position: fixed;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  --cardWidth: var(--cardWidthBigger);
`;

export default function PlayerStack() {
  const { player, currentPlayer, players, playerId } = useSelector((state) => ({
    player: state.game.players[0],
    currentPlayer: state.game.currentPlayer,
    players: state.game.players,
    playerId: state.game.playerId,
  }));
  const cards = player?.cards || [];

  // Determine spectating: playerId exists but is not one of the seated players
  const spectating = Array.isArray(players) && playerId && !players.some((p) => p && p.id === playerId);

  // When spectating, force all hand cards to non-playable (no clicks)
  const displayCards = spectating
    ? cards.map((c) => ({ ...c, playable: false }))
    : cards;

  return (
    <Root>
      <CardsRow
        cards={displayCards}
        highlight={currentPlayer === 0 && !spectating}
        cardProps={{ selectable: !spectating }}
      />
      {player?.isBot && player?.llmProvider ? (
        <div
          style={{
            position: 'fixed',
            bottom: 200,
            left: '50%',
            transform: 'translateX(-50%)',
            fontSize: 12,
            color: '#bbb',
            background: 'rgba(0,0,0,0.4)',
            padding: '2px 6px',
            borderRadius: 6,
            pointerEvents: 'none',
          }}
        >
          {player.name} ({player.llmProvider}{player.llmModel ? `:${player.llmModel}` : ''})
        </div>
      ) : null}
    </Root>
  );
}
