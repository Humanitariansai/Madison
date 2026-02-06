import React from 'react';
import { InspectionResult, InspectionLevel } from '../types';
import { AlertTriangle, Info, CheckCircle, XCircle, Type, Palette, Image as ImageIcon, ShieldCheck } from 'lucide-react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";

interface Props {
  violations: InspectionResult[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const CategoryMap: Record<string, { label: string; icon: React.ReactNode }> = {
  'PALETTE': { label: 'Color', icon: <Palette size={16} /> },
  'TYPOGRAPHY': { label: 'Typography', icon: <Type size={16} /> },
  'TEXT_BODY': { label: 'Typography', icon: <Type size={16} /> },
  'SPACING': { label: 'Typography', icon: <Type size={16} /> },
  'LOGO': { label: 'Logo', icon: <ShieldCheck size={16} /> },
  'IMAGERY': { label: 'Imagery', icon: <ImageIcon size={16} /> },
};

const LevelIcon: React.FC<{ level: InspectionLevel }> = ({ level }) => {
  switch (level) {
    case 'CRITICAL': return <XCircle size={14} className="text-destructive shrink-0" />;
    case 'MEDIUM': return <AlertTriangle size={14} className="text-amber-500 shrink-0" />;
    case 'LOW': return <Info size={14} className="text-blue-500 shrink-0" />;
    case 'PASS': return <CheckCircle size={14} className="text-green-500 shrink-0" />;
    default: return <Info size={14} className="text-muted-foreground shrink-0" />;
  }
};

export const ViolationSidebar: React.FC<Props> = ({ violations, selectedId, onSelect }) => {
  const [openAccordion, setOpenAccordion] = React.useState<string | undefined>(undefined);
  const [containerHeight, setContainerHeight] = React.useState<number>(0);
  const accordionContainerRef = React.useRef<HTMLDivElement>(null);

  // Group violations by mapped category
  const groupedViolations = violations.reduce((acc, v) => {
    const categoryKey = CategoryMap[v.type] ? CategoryMap[v.type].label : 'Other';
    if (!acc[categoryKey]) acc[categoryKey] = [];
    acc[categoryKey].push(v);
    return acc;
  }, {} as Record<string, InspectionResult[]>);

  // Define order of groups as requested
  const groupOrder = ['Logo', 'Typography', 'Color', 'Imagery', 'Other'];

  // Filter to only groups that have items
  const availableGroups = groupOrder.filter(group => {
    const items = groupedViolations[group];
    return items && items.length > 0;
  });

  // Measure container height
  React.useEffect(() => {
    const measureHeight = () => {
      if (accordionContainerRef.current) {
        setContainerHeight(accordionContainerRef.current.clientHeight);
      }
    };

    measureHeight();
    window.addEventListener('resize', measureHeight);
    return () => window.removeEventListener('resize', measureHeight);
  }, []);

  // Set first group as default open on mount
  React.useEffect(() => {
    if (availableGroups.length > 0 && openAccordion === undefined) {
      setOpenAccordion(availableGroups[0]);
    }
  }, [availableGroups, openAccordion]);

  const issueCount = violations.filter(v => v.status === 'FAIL').length;
  const passCount = violations.length - issueCount;

  if (violations.length === 0) {
    return (
      <div className="w-full shrink-0 bg-background h-full flex flex-col items-center justify-center text-center p-8 text-muted-foreground">
        <CheckCircle size={48} className="text-muted-foreground/20 mb-4" />
        <h3 className="font-semibold text-foreground mb-1">No Items Detected</h3>
        <p className="text-sm">The inspection found no inspectable elements.</p>
      </div>
    );
  }

  return (
    <div className="w-full shrink-0 bg-background h-full flex flex-col shadow-sm z-20">
      <div className="p-4 border-b bg-muted/20 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-semibold text-foreground flex items-center gap-2">
            Inspection Tasks
          </h2>
          <Badge variant="outline" className="font-mono">
            {issueCount} Pending
          </Badge>
        </div>

        {/* Simple Progress Bar or Stats */}
        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden flex">
          <div className="bg-green-500 h-full transition-all duration-500" style={{ width: `${(passCount / violations.length) * 100}%` }} />
          <div className="bg-red-500 h-full transition-all duration-500" style={{ width: `${(issueCount / violations.length) * 100}%` }} />
        </div>
        <div className="flex justify-between text-[10px] text-muted-foreground mt-1.5">
          <span>{passCount} Passing</span>
          <span>{issueCount} Issues</span>
        </div>
      </div>


      <div ref={accordionContainerRef} className="flex-1 min-h-0 overflow-hidden bg-background">
        <Accordion
          type="single"
          collapsible
          value={openAccordion}
          onValueChange={setOpenAccordion}
          className="w-full"
        >
          {availableGroups.map((group, index) => {
            const groupItems = groupedViolations[group];
            if (!groupItems || groupItems.length === 0) return null;

            // Calculate dynamic max-height to keep all triggers visible
            // Total space needed for all accordion triggers
            const totalTriggerSpace = availableGroups.length * 48; // 48px per trigger
            const PADDING = 20; // Safety padding
            const maxContentHeight = containerHeight > 0
              ? `${containerHeight - totalTriggerSpace - PADDING}px`
              : '400px'; // Fallback while measuring

            // Determine group status (red if any critical/fail, else green)
            const groupIssues = groupItems.filter(i => i.status === 'FAIL').length;
            const hasIssues = groupIssues > 0;

            // Sort items: Failures first, then by level
            const sortedItems = [...groupItems].sort((a, b) => {
              if (a.status !== b.status) return a.status === 'FAIL' ? -1 : 1; // Fails first
              const weights = { CRITICAL: 4, MEDIUM: 3, LOW: 2, PASS: 1 };
              return weights[b.level] - weights[a.level];
            });

            return (
              <AccordionItem key={group} value={group} className="border-b px-0">
                <AccordionTrigger className="px-4 py-3 hover:bg-muted/50 hover:no-underline [&[data-state=open]]:bg-muted/20">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    { /* Find icon for group */}
                    {Object.values(CategoryMap).find(c => c.label === group)?.icon || <Info size={16} />}
                    {group}
                    <Badge variant={hasIssues ? "destructive" : "secondary"} className="ml-2 h-5 px-1.5 text-[10px] font-mono">
                      {groupIssues > 0 ? `${groupIssues} Issues` : 'Pass'}
                    </Badge>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="p-0">
                  <div
                    className="overflow-y-auto border-t bg-muted/5"
                    style={{ maxHeight: maxContentHeight }}
                  >
                    <div className="divide-y">
                      {sortedItems.map(v => (
                        <div
                          key={v.id}
                          onClick={() => onSelect(v.id)}
                          className={cn(
                            "flex gap-3 p-3 pl-8 cursor-pointer transition-colors relative",
                            selectedId === v.id ? "bg-primary/5" : "hover:bg-muted/50"
                          )}
                        >
                          {selectedId === v.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />}

                          <div className="mt-0.5">
                            <LevelIcon level={v.level} />
                          </div>
                          <div className="space-y-1">
                            <p className={cn("text-xs font-medium leading-normal", v.status === 'FAIL' ? "text-foreground" : "text-muted-foreground line-through opacity-70")}>
                              {v.message}
                            </p>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-muted-foreground uppercase">{v.type}</span>
                              <span className="text-[10px] text-muted-foreground">• Page {v.pageNumber}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </div>
    </div>
  );
};
