import { useParams } from "react-router";

export default function ProjectSettingsPage() {
  const { projectId } = useParams();
  return (
    <div className="p-6">
      <h3 className="text-2xl font-medium">Project Settings</h3>
      <p className="text-sm text-muted-foreground">
        Manage settings for project ID: {projectId}
      </p>
      <div className="mt-8">
        <p>Project settings configuration will appear here.</p>
      </div>
    </div>
  );
}
