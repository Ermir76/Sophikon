import { useMemo, useRef } from "react";

import { useMyOrgRole } from "@/features/organizations";
import { PageShell } from "@/shared/components/layout/PageShell";

import { SettingsAnchorNav } from "../components/SettingsAnchorNav";
import { SettingsLayout } from "../components/SettingsLayout";
import { AiPreferencesSection } from "../components/sections/AiPreferencesSection";
import { BillingSection } from "../components/sections/BillingSection";
import { GeneralSection } from "../components/sections/GeneralSection";
import { MembersSection } from "../components/sections/MembersSection";
import { NotificationsSection } from "../components/sections/NotificationsSection";
import { ProfileSection } from "../components/sections/ProfileSection";
import { SecuritySection } from "../components/sections/SecuritySection";
import { useActiveSection } from "../hooks/useActiveSection";

const BASE_SECTION_ORDER = [
  "profile",
  "security",
  "notifications",
  "ai-preferences",
  "general",
  "members",
  "billing",
] as const;

const SECTION_CARD_CLASS =
  "mx-auto w-full max-w-[52rem] rounded-xl border border-border/60 bg-transparent px-6 pb-5 pt-0";

export default function SettingsPage() {
  const { role } = useMyOrgRole();
  const isAdminOrOwner = role === "admin" || role === "owner";

  const profileRef = useRef<HTMLDivElement>(null);
  const securityRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const aiPreferencesRef = useRef<HTMLDivElement>(null);
  const generalRef = useRef<HTMLDivElement>(null);
  const membersRef = useRef<HTMLDivElement>(null);
  const billingRef = useRef<HTMLDivElement>(null);

  const refs = useMemo(
    () => ({
      profile: profileRef,
      security: securityRef,
      notifications: notificationsRef,
      "ai-preferences": aiPreferencesRef,
      general: generalRef,
      members: membersRef,
      billing: billingRef,
    }),
    [],
  );

  const sectionOrder = useMemo(
    () =>
      BASE_SECTION_ORDER.filter((sectionId) => {
        if (!isAdminOrOwner && (sectionId === "general" || sectionId === "members")) {
          return false;
        }
        return true;
      }),
    [isAdminOrOwner],
  );

  const activeSection = useActiveSection(refs, sectionOrder);

  const onSectionClick = (sectionId: string) => {
    const element = refs[sectionId]?.current;
    if (!element) {
      return;
    }

    element.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <PageShell className="h-full overflow-y-auto pt-0">
      <SettingsLayout
        anchorNav={
          <SettingsAnchorNav
            activeSection={activeSection}
            onSectionClick={onSectionClick}
            isAdminOrOwner={isAdminOrOwner}
          />
        }
      >
        <div className="space-y-6 p-4 md:px-0 md:py-10">
          <div ref={profileRef} data-section-id="profile" className={SECTION_CARD_CLASS}>
            <ProfileSection />
          </div>
          <div ref={securityRef} data-section-id="security" className={SECTION_CARD_CLASS}>
            <SecuritySection />
          </div>
          <div ref={notificationsRef} data-section-id="notifications" className={SECTION_CARD_CLASS}>
            <NotificationsSection />
          </div>
          <div ref={aiPreferencesRef} data-section-id="ai-preferences" className={SECTION_CARD_CLASS}>
            <AiPreferencesSection />
          </div>
          {isAdminOrOwner ? (
            <>
              <div ref={generalRef} data-section-id="general" className={SECTION_CARD_CLASS}>
                <GeneralSection />
              </div>
              <div ref={membersRef} data-section-id="members" className={SECTION_CARD_CLASS}>
                <MembersSection />
              </div>
            </>
          ) : null}
          <div ref={billingRef} data-section-id="billing" className={SECTION_CARD_CLASS}>
            <BillingSection />
          </div>
        </div>
      </SettingsLayout>
    </PageShell>
  );
}
