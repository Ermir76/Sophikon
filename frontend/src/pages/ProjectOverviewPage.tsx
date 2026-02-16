import { useParams } from "react-router";

export default function ProjectOverviewPage() {
  const { projectId } = useParams();

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <h1 className="text-2xl font-semibold">Project Overview</h1>
      <p className="text-muted-foreground">Overview for project {projectId}.</p>
    </div>
  );
}
