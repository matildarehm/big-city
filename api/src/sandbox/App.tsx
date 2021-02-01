import React from "react";
import io from "socket.io-client";

import MessageList from "./components/messages/MessageList";
import NewMessage from "./components/messages/NewMessage";

const socket = io(location.origin);

export default () => (
    <div>
        <MessageList socket={socket} />
        <NewMessage socket={socket} />
    </div>
);