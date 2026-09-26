import { redirect } from "next/navigation";

// AuthGuard in layout handles unauthenticated users → /login
// Authenticated users land here → send them to /digest
export default function Home() {
  redirect("/digest");
}
