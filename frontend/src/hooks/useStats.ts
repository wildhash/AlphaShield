import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchStats } from "../services/api";
import { useEffect } from "react";
import { connectSocket } from "../services/socket";

export function useStats() {
  const qc = useQueryClient();
  const q = useQuery(["stats"], fetchStats, { refetchInterval: 30000 });

  useEffect(() => {
    const socket = connectSocket();
    socket.on("connect", () => console.log("socket connected", socket.id));
    const handler = (data: any) => {
      qc.setQueryData(["stats"], data);
    };
    socket.on("stats:changed", handler);
    return () => {
      socket.off("stats:changed", handler);
    };
  }, [qc]);

  return q;
}