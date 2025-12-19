import { useLocation } from "react-router-dom";

export default function RagPage() {
  return (
    <div className="flex h-full flex-col gap-2 p-6">
      <div className="text-lg font-semibold"> {useLocation().pathname}</div>
    </div>
  );
}
