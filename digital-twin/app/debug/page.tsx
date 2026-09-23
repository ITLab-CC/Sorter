import DebugViewer from "./DebugViewer";

export default async function DebugPage({ searchParams }: PageProps<"/debug">) {
  const { part } = await searchParams;
  const parts = typeof part === "string" ? part.split(",") : Array.isArray(part) ? part : ["Kamera/main_chamber"];
  return <DebugViewer parts={parts} />;
}
