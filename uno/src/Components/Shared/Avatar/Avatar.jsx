import React from "react";
import styled from "styled-components";
const Cavatar = styled.div`
  /* Responsive fixed-size circle */
  width: clamp(96px, 18vw, 160px);
  height: clamp(96px, 18vw, 160px);
  border-radius: 50%;
  border: 1px solid rgb(0 3 24);
  box-shadow: 0px 0px 6px 3px rgb(23 25 41);
  overflow: hidden;
  position: relative;
  margin: 0 auto; /* center within grid cell */

  img {
    width: 100%;
    height: 100%;
    display: block;
    object-fit: cover;
    object-position: top;
  }
`;
const Avatar = ({ seed }) => {
  return (
    <Cavatar> 
      <img src={`https://api.dicebear.com/9.x/adventurer/svg?seed=${seed}`} alt="" />
    </Cavatar>
  );
};

export default Avatar;
