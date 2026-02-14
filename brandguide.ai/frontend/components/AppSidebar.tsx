"use client"

import * as React from "react"
import {
    BookOpen,
    Bot,
    Command,
    Frame,
    LifeBuoy,
    Map,
    PieChart,
    Send,
    Settings2,
    SquareTerminal,
    LayoutDashboard,
    FolderKanban,
    Palette
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavSecondary } from "@/components/nav-secondary"
import { NavUser } from "@/components/nav-user"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar"
import { Project, BrandKit } from "@/types"

const data = {
    user: {
        name: "John Doe",
        email: "john@brandguide.ai",
        avatar: "/avatars/shadcn.jpg",
    },
    navMain: [
        {
            title: "Platform",
            url: "#",
            icon: SquareTerminal,
            isActive: true, // Default open
            items: [
                {
                    title: "Dashboard",
                    url: "dashboard",
                },
                {
                    title: "Projects",
                    url: "projects",
                },
                {
                    title: "Brand Kits",
                    url: "kits",
                },
            ],
        },
        {
            title: "Settings",
            url: "#",
            icon: Settings2,
            items: [
                {
                    title: "General",
                    url: "settings",
                },
                {
                    title: "Team",
                    url: "#",
                },
                {
                    title: "Billing",
                    url: "#",
                },
            ],
        },
    ],
    navSecondary: [
        {
            title: "Support",
            url: "#",
            icon: LifeBuoy,
        },
        {
            title: "Feedback",
            url: "#",
            icon: Send,
        },
    ],
    // We will map recent projects dynamically if needed, for now placeholders to match style
    projects: [
        {
            name: "Q1 Marketing Audit",
            url: "#",
            icon: Frame,
        },
        {
            name: "Rebranding 2024",
            url: "#",
            icon: PieChart,
        },
        {
            name: "Social Media Campaign",
            url: "#",
            icon: Map,
        },
    ],
}

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
    activeTab: 'dashboard' | 'projects' | 'kits' | 'settings';
    setActiveTab: (tab: 'dashboard' | 'projects' | 'kits' | 'settings') => void;
    projects: Project[];
    brandKits: BrandKit[];
}

export function AppSidebar({ activeTab, setActiveTab, projects: propProjects, brandKits, ...props }: AppSidebarProps) {
    // Pass setActiveTab down to NavMain to handle routing
    return (
        <Sidebar variant="inset" {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" asChild>
                            <a href="#">
                                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                                    <Command className="size-4" />
                                </div>
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-medium">BrandGuide AI</span>
                                    <span className="truncate text-xs">Enterprise</span>
                                </div>
                            </a>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent>
                <NavMain items={data.navMain} activeTab={activeTab} onTabChange={setActiveTab as any} />
                {/* <NavProjects projects={data.projects} /> */}
                <NavSecondary items={data.navSecondary} className="mt-auto" />
            </SidebarContent>
            <SidebarFooter>
                <NavUser user={data.user} />
            </SidebarFooter>
        </Sidebar>
    )
}
