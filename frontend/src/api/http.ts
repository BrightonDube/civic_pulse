import axios from "axios";
import { env } from "../config/env";

export const http = axios.create({
  baseURL: env.apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
});
