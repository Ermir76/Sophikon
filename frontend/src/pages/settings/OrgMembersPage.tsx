import { useEffect, useState, useCallback } from "react";
import { Plus, MoreHorizontal, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

import { organizationService } from "@/services/organization";
import { useOrgStore } from "@/store/org-store";
import type { OrganizationMember, OrgRole } from "@/types/organization";

const inviteSchema = z.object({
  email: z.email("Invalid email address"),
  role: z.enum(["owner", "admin", "member"]),
});

type InviteFormValues = z.infer<typeof inviteSchema>;

export default function OrgMembersPage() {
  const { activeOrganization } = useOrgStore();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);

  // UI states for actions
  const [memberToRemove, setMemberToRemove] =
    useState<OrganizationMember | null>(null);
  const [memberToEdit, setMemberToEdit] = useState<OrganizationMember | null>(
    null,
  );
  const [targetRole, setTargetRole] = useState<OrgRole | null>(null);

  const form = useForm<InviteFormValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: {
      email: "",
      role: "member",
    },
  });

  const fetchMembers = useCallback(async () => {
    if (!activeOrganization) return;
    setLoading(true);
    try {
      const response = await organizationService.listMembers(
        activeOrganization.id,
      );
      setMembers(response.items);
    } catch (error) {
      toast.error("Error", {
        description: "Failed to fetch members.",
      });
    } finally {
      setLoading(false);
    }
  }, [activeOrganization]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]); // Adding fetchMembers as dependency since it's memoized

  const onInvite = async (data: InviteFormValues) => {
    if (!activeOrganization) return;
    try {
      await organizationService.inviteMember(activeOrganization.id, data);
      toast.success("Invitation sent", {
        description: `Invited ${data.email} as ${data.role}.`,
      });
      setInviteOpen(false);
      form.reset();
      await fetchMembers();
    } catch (error) {
      toast.error("Error", {
        description: "Failed to invite member.",
      });
    }
  };

  const confirmRemoveMember = async () => {
    if (!activeOrganization || !memberToRemove) return;
    await onRemoveMember(memberToRemove.id);
    setMemberToRemove(null);
  };

  const onRemoveMember = async (memberId: string) => {
    if (!activeOrganization) return;
    try {
      await organizationService.removeMember(activeOrganization.id, memberId);
      toast.success("Member removed", {
        description: "The member has been removed from the organization.",
      });
      await fetchMembers();
    } catch (error) {
      toast.error("Error", {
        description: "Failed to remove member.",
      });
    }
  };

  const onUpdateRole = async () => {
    if (!activeOrganization || !memberToEdit || !targetRole) return;
    try {
      await organizationService.updateMemberRole(
        activeOrganization.id,
        memberToEdit.id,
        { role: targetRole },
      );
      toast.success("Role updated", {
        description: `${memberToEdit.user_full_name || memberToEdit.user_email}'s role updated to ${targetRole}.`,
      });
      setMemberToEdit(null);
      setTargetRole(null);
      await fetchMembers();
    } catch (error) {
      toast.error("Error", {
        description: "Failed to update member role.",
      });
    }
  };

  if (!activeOrganization) {
    return <div className="p-4">Please select an organization.</div>;
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-medium">Members</h3>
          <p className="text-sm text-muted-foreground">
            Manage who has access to this organization.
          </p>
        </div>
        <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 size-4" />
              Invite Member
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite Member</DialogTitle>
              <DialogDescription>
                Send an invitation to join {activeOrganization.name}.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onInvite)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input placeholder="colleague@example.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="role"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Role</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a role" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="owner">Owner</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="member">Member</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button type="submit">Send Invitation</Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      <Separator />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead className="w-[100px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && members.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="h-24 text-center">
                    <Loader2 className="mx-auto size-6 animate-spin" />
                  </TableCell>
                </TableRow>
              ) : members.length === 0 && !loading ? (
                <TableRow>
                  <TableCell colSpan={3} className="h-24 text-center">
                    No members found.
                  </TableCell>
                </TableRow>
              ) : (
                members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {member.user_full_name || "Unknown"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {member.user_email || "No Email"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="capitalize">{member.role}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="size-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => {
                              if (member.user_email)
                                navigator.clipboard.writeText(
                                  member.user_email,
                                );
                            }}
                          >
                            Copy Email
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => {
                              setMemberToEdit(member);
                              setTargetRole(member.role);
                            }}
                          >
                            Change Role
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setMemberToRemove(member)}
                          >
                            Remove Member
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Remove Confirmation Dialog */}
      <AlertDialog
        open={!!memberToRemove}
        onOpenChange={(open) => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove{" "}
              {memberToRemove?.user_full_name || memberToRemove?.user_email}{" "}
              from the organization. They will lose access to all projects
              immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmRemoveMember}
              className="bg-destructive hover:bg-destructive/90"
            >
              Remove Member
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Change Role Dialog */}
      <Dialog
        open={!!memberToEdit}
        onOpenChange={(open) => !open && setMemberToEdit(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Role</DialogTitle>
            <DialogDescription>
              Update the role for{" "}
              {memberToEdit?.user_full_name || memberToEdit?.user_email}.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="role" className="text-right text-sm font-medium">
                Role
              </label>
              <Select
                value={targetRole || memberToEdit?.role || "member"}
                onValueChange={(val) => setTargetRole(val as OrgRole)}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="owner">Owner</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="member">Member</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" onClick={onUpdateRole}>
              Update Role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
