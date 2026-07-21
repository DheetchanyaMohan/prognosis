import type { ReactNode } from "react"
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui"
import type { RunConfig } from "../types"

interface ConfigPanelProps {
  config: RunConfig
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-mono text-foreground">{children}</dd>
    </div>
  )
}

/**
 * Always present (Architecture §7.4) — rendered the moment `config`
 * arrives, since it never waits on summary/diagnostics. Structured,
 * labeled key-value layout grouped by dataset/model/training,
 * monospace values — never raw JSON. Reference material: deliberately
 * quiet, never competing visually with the diagnosis (§10).
 */
export function ConfigPanel({ config }: ConfigPanelProps) {
  const { dataset, model, training } = config

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <Card className="p-4">
        <CardHeader className="p-0">
          <CardTitle>Dataset</CardTitle>
        </CardHeader>
        <CardContent className="p-0 pt-2">
          <dl>
            <Row label="Train size">{dataset.train_size}</Row>
            <Row label="Val size">{dataset.val_size}</Row>
            <Row label="Augmentation">{dataset.augmentation ? "enabled" : "disabled"}</Row>
          </dl>
        </CardContent>
      </Card>

      <Card className="p-4">
        <CardHeader className="p-0">
          <CardTitle>Model</CardTitle>
        </CardHeader>
        <CardContent className="p-0 pt-2">
          <dl>
            <Row label="Dropout">{model.dropout}</Row>
            <Row label="Seed">{config.seed}</Row>
          </dl>
        </CardContent>
      </Card>

      <Card className="p-4">
        <CardHeader className="p-0">
          <CardTitle>Training</CardTitle>
        </CardHeader>
        <CardContent className="p-0 pt-2">
          <dl>
            <Row label="Optimizer">
              <Badge tone="neutral">{training.optimizer}</Badge>
            </Row>
            <Row label="LR">{training.lr}</Row>
            <Row label="LR scheduler">
              <Badge tone="neutral">{training.lr_scheduler}</Badge>
            </Row>
            <Row label="Batch size">{training.batch_size}</Row>
            <Row label="Weight decay">{training.weight_decay}</Row>
            <Row label="Epochs">{training.epochs}</Row>
            <Row label="Gradient clip norm">
              {training.gradient_clip_norm === null ? "disabled" : training.gradient_clip_norm}
            </Row>
            <Row label="Early stop on divergence">
              {training.early_stop_on_divergence ? "enabled" : "disabled"}
            </Row>
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}
