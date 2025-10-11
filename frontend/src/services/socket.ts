import { io } from "socket.io-client";
let socket: any = null;
export function connectSocket() {
  if (!socket) {
    socket = io(import.meta.env.VITE_API_BASE || "http://localhost:4000");
  }
  return socket;
}

export function getSocket() { return socket; }