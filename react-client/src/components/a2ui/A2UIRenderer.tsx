import React, { Component, type ErrorInfo, type ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, RefreshCw } from "lucide-react";

// =============================================================================
// Error Boundary Component
// =============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onRetry?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class A2UIErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[A2UI Error Boundary] Rendering error:", error);
    console.error("[A2UI Error Boundary] Component stack:", errorInfo.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Alert variant="destructive" className="my-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Unable to render UI</AlertTitle>
          <AlertDescription className="mt-2">
            <p className="mb-2">Something went wrong while displaying the agent's response.</p>
            <Button
              variant="outline"
              size="sm"
              onClick={this.handleRetry}
              className="gap-2"
            >
              <RefreshCw className="h-3 w-3" />
              Try Again
            </Button>
          </AlertDescription>
        </Alert>
      );
    }

    return this.props.children;
  }
}

// =============================================================================
// Error Fallback Component (for validation errors)
// =============================================================================

interface A2UIErrorFallbackProps {
  message: string;
  details?: string;
}

function A2UIErrorFallback({ message, details }: A2UIErrorFallbackProps) {
  return (
    <Alert variant="destructive" className="my-4">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>UI Rendering Error</AlertTitle>
      <AlertDescription>
        <p>{message}</p>
        {details && (
          <details className="mt-2 text-xs">
            <summary className="cursor-pointer">Technical Details</summary>
            <pre className="mt-1 p-2 bg-muted rounded text-wrap break-all">{details}</pre>
          </details>
        )}
      </AlertDescription>
    </Alert>
  );
}

// =============================================================================
// Text Sanitization Utilities
// =============================================================================

/**
 * Sanitize text content to prevent XSS and malicious content.
 * - Strips HTML tags
 * - Removes javascript: and data: URLs
 * - Limits text length
 */
const MAX_TEXT_LENGTH = 10000; // Reasonable limit for displayed text

function sanitizeText(text: string): string {
  if (!text || typeof text !== 'string') return '';

  let sanitized = text;

  // Strip HTML tags (basic XSS prevention)
  sanitized = sanitized.replace(/<[^>]*>/g, '');

  // Remove javascript: and data: URLs which could be dangerous
  sanitized = sanitized.replace(/javascript:/gi, '');
  sanitized = sanitized.replace(/data:/gi, '');
  sanitized = sanitized.replace(/vbscript:/gi, '');

  // Remove on* event handlers that might slip through
  sanitized = sanitized.replace(/on\w+\s*=/gi, '');

  // Truncate overly long text
  if (sanitized.length > MAX_TEXT_LENGTH) {
    sanitized = sanitized.substring(0, MAX_TEXT_LENGTH) + '...';
    console.warn(`[A2UI Sanitizer] Truncated text from ${text.length} to ${MAX_TEXT_LENGTH} characters`);
  }

  return sanitized;
}

/**
 * Sanitize URLs to allow only safe protocols
 */
export function sanitizeUrl(url: string): string {
  if (!url || typeof url !== 'string') return '';

  // Only allow http, https, and relative URLs
  const lowerUrl = url.toLowerCase().trim();
  if (lowerUrl.startsWith('javascript:') ||
    lowerUrl.startsWith('data:') ||
    lowerUrl.startsWith('vbscript:')) {
    console.warn(`[A2UI Sanitizer] Blocked dangerous URL: ${url.substring(0, 50)}`);
    return '';
  }

  return url;
}

// =============================================================================
// Schema Validation
// =============================================================================

const VALID_COMPONENT_TYPES = [
  'Text', 'Image', 'Icon', 'Video', 'AudioPlayer',
  'Row', 'Column', 'List', 'Card', 'Tabs', 'Divider', 'Modal',
  'Button', 'CheckBox', 'TextField', 'DateTimeInput', 'MultipleChoice', 'Slider'
] as const;

interface ValidationError {
  path: string;
  message: string;
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

/**
 * Validate A2UI JSON structure before rendering
 */
export function validateA2UIJson(a2uiJson: any[]): ValidationResult {
  const errors: ValidationError[] = [];

  if (!Array.isArray(a2uiJson)) {
    return { valid: false, errors: [{ path: 'root', message: 'A2UI JSON must be an array' }] };
  }

  a2uiJson.forEach((message, msgIndex) => {
    const msgPath = `[${msgIndex}]`;

    // Validate surfaceUpdate
    if (message.surfaceUpdate) {
      const su = message.surfaceUpdate;

      if (!su.surfaceId) {
        errors.push({ path: `${msgPath}.surfaceUpdate`, message: 'Missing required field: surfaceId' });
      }

      if (!su.components || !Array.isArray(su.components)) {
        errors.push({ path: `${msgPath}.surfaceUpdate`, message: 'Missing or invalid components array' });
      } else {
        su.components.forEach((comp: any, compIndex: number) => {
          const compPath = `${msgPath}.surfaceUpdate.components[${compIndex}]`;

          if (!comp.id) {
            errors.push({ path: compPath, message: 'Component missing required field: id' });
          }

          if (!comp.component) {
            errors.push({ path: compPath, message: 'Component missing required field: component' });
          } else {
            const componentType = Object.keys(comp.component)[0];
            if (componentType && !VALID_COMPONENT_TYPES.includes(componentType as any)) {
              errors.push({
                path: `${compPath}.component`,
                message: `Unknown component type: "${componentType}". Valid types: ${VALID_COMPONENT_TYPES.join(', ')}`
              });
            }

            // Validate required fields per component type
            validateComponentFields(comp.component, componentType, `${compPath}.component.${componentType}`, errors);
          }
        });
      }
    }

    // Validate beginRendering
    if (message.beginRendering) {
      const br = message.beginRendering;

      if (!br.surfaceId) {
        errors.push({ path: `${msgPath}.beginRendering`, message: 'Missing required field: surfaceId' });
      }
      if (!br.root) {
        errors.push({ path: `${msgPath}.beginRendering`, message: 'Missing required field: root' });
      }
    }

    // Validate dataModelUpdate
    if (message.dataModelUpdate) {
      const dmu = message.dataModelUpdate;

      if (!dmu.surfaceId) {
        errors.push({ path: `${msgPath}.dataModelUpdate`, message: 'Missing required field: surfaceId' });
      }
      if (!dmu.contents || !Array.isArray(dmu.contents)) {
        errors.push({ path: `${msgPath}.dataModelUpdate`, message: 'Missing or invalid contents array' });
      }
    }
  });

  return { valid: errors.length === 0, errors };
}

function validateComponentFields(
  component: any,
  type: string,
  path: string,
  errors: ValidationError[]
) {
  if (!component || !type) return;

  const fields = component[type];
  if (!fields) return;

  // Required fields per component type
  switch (type) {
    case 'Button':
      if (!fields.child) {
        errors.push({ path, message: 'Button missing required field: child' });
      }
      if (!fields.action) {
        errors.push({ path, message: 'Button missing required field: action' });
      } else if (!fields.action.name) {
        errors.push({ path: `${path}.action`, message: 'Button action missing required field: name' });
      }
      break;

    case 'Text':
      if (!fields.text) {
        errors.push({ path, message: 'Text missing required field: text' });
      }
      break;

    case 'TextField':
      if (!fields.label) {
        errors.push({ path, message: 'TextField missing required field: label' });
      }
      break;

    case 'Image':
      if (!fields.url) {
        errors.push({ path, message: 'Image missing required field: url' });
      }
      break;

    case 'Row':
    case 'Column':
    case 'List':
      if (!fields.children) {
        errors.push({ path, message: `${type} missing required field: children` });
      }
      break;

    case 'Card':
      if (!fields.child) {
        errors.push({ path, message: 'Card missing required field: child' });
      }
      break;
  }
}

// =============================================================================
// Main A2UI Renderer
// =============================================================================

interface A2UIRendererProps {
  a2uiJson: any[];
  onAction: (actionName: string, context: Record<string, any>) => void;
  dataModel: Record<string, any>;
  onDataChange: (path: string, value: any) => void;
}

export function A2UIRenderer({ a2uiJson, onAction, dataModel, onDataChange }: A2UIRendererProps) {
  // Early return for empty/null input
  if (!a2uiJson || a2uiJson.length === 0) {
    console.debug("[A2UI] No A2UI JSON to render");
    return null;
  }

  // Validate that a2uiJson is actually an array
  if (!Array.isArray(a2uiJson)) {
    console.error("[A2UI] Invalid input: expected array, got", typeof a2uiJson);
    return (
      <A2UIErrorFallback
        message="Invalid UI data received from agent."
        details={`Expected array, received ${typeof a2uiJson}`}
      />
    );
  }

  // Run schema validation and log warnings
  const validationResult = validateA2UIJson(a2uiJson);
  if (!validationResult.valid) {
    console.warn("[A2UI] Schema validation warnings:", validationResult.errors);
    // Log each error individually for easier debugging
    validationResult.errors.forEach((err, i) => {
      console.warn(`  [${i + 1}] ${err.path}: ${err.message}`);
    });
  }

  // Find surfaceUpdate and beginRendering to get components and root
  let components: any[] = [];
  let rootId: string | null = null;

  for (const message of a2uiJson) {
    if (message.surfaceUpdate?.components) {
      components = message.surfaceUpdate.components;
    }
    if (message.beginRendering?.root) {
      rootId = message.beginRendering.root;
    }
  }

  // Log component parsing
  console.debug(`[A2UI] Found ${components.length} components${rootId ? `, root: ${rootId}` : ''}`);

  if (components.length === 0) {
    console.warn("[A2UI] No components found in surfaceUpdate");
    return (
      <A2UIErrorFallback
        message="No UI components to display."
        details="The agent response contained no renderable components."
      />
    );
  }

  // Build component map by ID
  const componentMap = new Map<string, any>();
  for (const comp of components) {
    if (comp.id) {
      componentMap.set(comp.id, comp.component);
    }
  }

  // Render from root with error boundary
  if (rootId && componentMap.has(rootId)) {
    return (
      <A2UIErrorBoundary>
        <div className="space-y-4">
          {renderComponentById(rootId, componentMap, onAction, dataModel, onDataChange)}
        </div>
      </A2UIErrorBoundary>
    );
  }

  // Fallback: render all components with error boundary
  return (
    <A2UIErrorBoundary>
      <div className="space-y-4">
        {components.map((comp: any) =>
          renderComponent(comp.component, comp.id, 0, componentMap, onAction, dataModel, onDataChange)
        )}
      </div>
    </A2UIErrorBoundary>
  );
}

// Export helper to process dataModelUpdate messages
export function processDataModelUpdates(a2uiJson: any[], currentDataModel: Record<string, any>): Record<string, any> {
  const newModel = { ...currentDataModel };

  for (const message of a2uiJson) {
    if (message.dataModelUpdate) {
      const { contents } = message.dataModelUpdate;
      if (contents && Array.isArray(contents)) {
        contents.forEach((item: any) => {
          if (item.key && item.valueMap) {
            newModel[item.key] = {};
            item.valueMap.forEach((vm: any) => {
              if (vm.key) {
                newModel[item.key][vm.key] = vm.valueString || vm.valueNumber || '';
              }
            });
          }
        });
      }
    }
  }

  return newModel;
}

// Render a component by its ID from the component map
function renderComponentById(
  id: string,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
): React.ReactNode {
  const component = componentMap.get(id);
  if (!component) return null;
  return renderComponent(component, id, 0, componentMap, onAction, dataModel, onDataChange);
}

function renderComponent(
  component: any,
  id: string,
  _index: number,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
): React.ReactNode {
  if (!component) return null;

  // Card component
  if (component.Card) {
    return renderCard(component.Card, id, componentMap, onAction, dataModel, onDataChange);
  }

  // Button component
  if (component.Button) {
    return renderButton(component.Button, id, componentMap, onAction, dataModel);
  }

  // TextField component
  if (component.TextField) {
    return renderTextField(component.TextField, id, dataModel, onDataChange);
  }

  // Text component
  if (component.Text) {
    return renderText(component.Text, id, dataModel);
  }

  // Row component
  if (component.Row) {
    return renderRow(component.Row, id, componentMap, onAction, dataModel, onDataChange);
  }

  // Column component
  if (component.Column) {
    return renderColumn(component.Column, id, componentMap, onAction, dataModel, onDataChange);
  }

  // List component (similar to Column but with different semantics)
  if (component.List) {
    return renderList(component.List, id, componentMap, onAction, dataModel, onDataChange);
  }

  // Divider component
  if (component.Divider) {
    return renderDivider(component.Divider, id);
  }

  // Icon component
  if (component.Icon) {
    return renderIcon(component.Icon, id, dataModel);
  }

  // Image component
  if (component.Image) {
    return renderImage(component.Image, id, dataModel);
  }

  // CheckBox component
  if (component.CheckBox) {
    return renderCheckBox(component.CheckBox, id, dataModel, onDataChange);
  }

  // DateTimeInput component
  if (component.DateTimeInput) {
    return renderDateTimeInput(component.DateTimeInput, id, dataModel, onDataChange);
  }

  // Log unknown component types for debugging
  const componentType = Object.keys(component)[0] || 'unknown';
  console.warn(`[A2UI] Unknown component type: "${componentType}" (id: ${id})`, component);

  // Render a placeholder in development to make issues visible
  return (
    <div
      key={id}
      className="border border-dashed border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded text-xs text-yellow-700 dark:text-yellow-300"
    >
      ⚠️ Unsupported: {componentType}
    </div>
  );
}

function renderCard(
  card: any,
  id: string,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  // A2UI Card uses "child" (single ID) not "components"
  const childId = card.child;

  return (
    <Card key={id} className="w-full">
      <CardContent className="p-4">
        {childId && renderComponentById(childId, componentMap, onAction, dataModel, onDataChange)}
      </CardContent>
    </Card>
  );
}

function renderButton(
  button: any,
  id: string,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>
) {
  // Button can have a "child" ID for its label text
  const childId = button.child;
  let label = '';

  if (childId) {
    const childComponent = componentMap.get(childId);
    if (childComponent?.Text) {
      label = resolveValue(childComponent.Text.text, dataModel);
    }
  } else if (button.label) {
    label = resolveValue(button.label, dataModel);
  }

  const action = button.action;

  // Map A2UI variant to shadcn variant
  const variantMap: Record<string, "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"> = {
    "primary": "default",
    "destructive": "destructive",
    "outline": "outline",
    "secondary": "secondary",
    "ghost": "ghost",
    "link": "link"
  };

  // Determine variant: explicit variant > primary boolean > default
  let variant: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" = "default";
  if (button.variant && variantMap[button.variant]) {
    variant = variantMap[button.variant];
  } else if (button.primary === false) {
    variant = "outline";  // Non-primary = outline
  }
  // If primary is true or not specified, use "default" (blue filled)

  const handleClick = () => {
    if (action) {
      const context: Record<string, any> = {};

      if (action.context) {
        action.context.forEach((ctx: any) => {
          context[ctx.key] = resolveValue(ctx.value, dataModel);
        });
      }

      onAction(action.name, context);
    }
  };

  return (
    <Button key={id} variant={variant} onClick={handleClick}>
      {label}
    </Button>
  );
}

function renderTextField(
  textField: any,
  id: string,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  const label = resolveValue(textField.label, dataModel);
  const textPath = textField.text?.path;
  const value = textPath ? getValueFromPath(dataModel, textPath) : '';

  return (
    <div key={id} className="space-y-2">
      {label && <label className="text-sm font-medium">{label}</label>}
      <Input
        value={value || ''}
        onChange={(e) => {
          if (textPath) {
            onDataChange(textPath, e.target.value);
          }
        }}
        placeholder={label}
      />
    </div>
  );
}

function renderText(text: any, id: string, dataModel: Record<string, any>) {
  const content = resolveValue(text.text, dataModel);
  const usageHint = text.usageHint || 'body';

  const classMap: Record<string, string> = {
    h1: 'text-2xl font-bold',
    h2: 'text-xl font-semibold',
    h3: 'text-lg font-semibold',
    body: 'text-base',
    caption: 'text-sm text-muted-foreground',
  };

  const className = classMap[usageHint] || 'text-base';

  return (
    <div key={id} className={className}>
      {content}
    </div>
  );
}

function renderRow(
  row: any,
  id: string,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  // A2UI Row uses "children.explicitList" array of IDs
  const childIds = row.children?.explicitList || [];
  const distribution = row.distribution;

  let className = "flex flex-row gap-4 items-center";
  if (distribution === "spaceBetween") {
    className = "flex flex-row justify-between items-center w-full";
  }

  return (
    <div key={id} className={className}>
      {childIds.map((childId: string) =>
        renderComponentById(childId, componentMap, onAction, dataModel, onDataChange)
      )}
    </div>
  );
}

function renderColumn(
  column: any,
  id: string,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  // A2UI Column uses "children.explicitList" array of IDs
  const childIds = column.children?.explicitList || [];

  return (
    <div key={id} className="flex flex-col gap-4">
      {childIds.map((childId: string) =>
        renderComponentById(childId, componentMap, onAction, dataModel, onDataChange)
      )}
    </div>
  );
}

function resolveValue(value: any, dataModel: Record<string, any>, shouldSanitize: boolean = true): string {
  if (!value) return '';

  let result = '';

  if (value.literalString) {
    result = value.literalString;
  } else if (value.path) {
    result = getValueFromPath(dataModel, value.path) || '';
  }

  // Sanitize text content unless explicitly disabled
  return shouldSanitize ? sanitizeText(result) : result;
}

function getValueFromPath(dataModel: Record<string, any>, path: string): any {
  // Path format: /key1/key2
  const parts = path.split('/').filter(p => p);
  let current = dataModel;
  let traversedPath = '';

  for (const part of parts) {
    traversedPath += '/' + part;
    if (current && typeof current === 'object') {
      if (!(part in current)) {
        console.debug(`[A2UI Data Model] Missing path segment: "${part}" at "${traversedPath}" (full path: "${path}")`);
        return undefined;
      }
      current = current[part];
    } else {
      console.debug(`[A2UI Data Model] Cannot traverse path "${path}" - hit non-object at "${traversedPath}"`);
      return undefined;
    }
  }

  if (current === undefined) {
    console.debug(`[A2UI Data Model] Path "${path}" resolved to undefined`);
  }

  return current;
}

// =============================================================================
// Additional Component Renderers
// =============================================================================

function renderList(
  list: any,
  id: string,
  componentMap: Map<string, any>,
  onAction: (actionName: string, context: Record<string, any>) => void,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  // A2UI List uses "children.explicitList" array of IDs
  const childIds = list.children?.explicitList || [];
  const direction = list.direction || 'vertical';

  const className = direction === 'horizontal'
    ? 'flex flex-row gap-4 flex-wrap'
    : 'flex flex-col gap-2';

  return (
    <div key={id} className={className}>
      {childIds.map((childId: string) =>
        renderComponentById(childId, componentMap, onAction, dataModel, onDataChange)
      )}
    </div>
  );
}

function renderDivider(divider: any, id: string) {
  const axis = divider.axis || 'horizontal';

  if (axis === 'vertical') {
    return <div key={id} className="w-px bg-border h-full min-h-[20px]" />;
  }

  return <hr key={id} className="border-t border-border my-2" />;
}

function renderIcon(icon: any, id: string, dataModel: Record<string, any>) {
  const iconName = resolveValue(icon.name, dataModel, false);

  // Map A2UI icon names to lucide-react icons
  // For now, render as a placeholder with the icon name
  const iconClasses = "w-5 h-5 text-muted-foreground";

  // Common icon mappings
  const iconMap: Record<string, string> = {
    'check': '✓',
    'close': '✕',
    'add': '+',
    'calendarToday': '📅',
    'event': '📅',
    'person': '👤',
    'accountCircle': '👤',
    'mail': '✉️',
    'phone': '📞',
    'call': '📞',
    'locationOn': '📍',
    'info': 'ℹ️',
    'warning': '⚠️',
    'error': '❌',
    'favorite': '❤️',
    'star': '⭐',
    'settings': '⚙️',
    'search': '🔍',
    'home': '🏠',
    'arrowBack': '←',
    'arrowForward': '→',
  };

  const iconSymbol = iconMap[iconName] || `[${iconName}]`;

  return (
    <span key={id} className={iconClasses} role="img" aria-label={iconName}>
      {iconSymbol}
    </span>
  );
}

function renderImage(image: any, id: string, dataModel: Record<string, any>) {
  const url = resolveValue(image.url, dataModel, false);
  const sanitizedUrl = sanitizeUrl(url);

  if (!sanitizedUrl) {
    console.warn(`[A2UI] Image blocked - invalid or dangerous URL: ${url?.substring(0, 50)}`);
    return null;
  }

  const fit = image.fit || 'contain';
  const usageHint = image.usageHint || 'mediumFeature';

  // Map usage hints to size classes
  const sizeMap: Record<string, string> = {
    'icon': 'w-6 h-6',
    'avatar': 'w-10 h-10 rounded-full',
    'smallFeature': 'w-24 h-24',
    'mediumFeature': 'w-48 h-48',
    'largeFeature': 'w-full max-w-md',
    'header': 'w-full h-32',
  };

  const sizeClass = sizeMap[usageHint] || 'w-48 h-48';

  return (
    <img
      key={id}
      src={sanitizedUrl}
      alt=""
      className={`${sizeClass} object-${fit}`}
      loading="lazy"
    />
  );
}

function renderCheckBox(
  checkbox: any,
  id: string,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  const label = resolveValue(checkbox.label, dataModel);
  const valuePath = checkbox.value?.path;
  const isChecked = valuePath
    ? Boolean(getValueFromPath(dataModel, valuePath))
    : Boolean(checkbox.value?.literalBoolean);

  return (
    <label key={id} className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={isChecked}
        onChange={(e) => {
          if (valuePath) {
            onDataChange(valuePath, e.target.checked);
          }
        }}
        className="w-4 h-4"
      />
      <span className="text-sm">{label}</span>
    </label>
  );
}

function renderDateTimeInput(
  dateTime: any,
  id: string,
  dataModel: Record<string, any>,
  onDataChange: (path: string, value: any) => void
) {
  const valuePath = dateTime.value?.path;
  const value = valuePath
    ? getValueFromPath(dataModel, valuePath) || ''
    : dateTime.value?.literalString || '';

  const enableDate = dateTime.enableDate !== false; // Default true
  const enableTime = dateTime.enableTime !== false; // Default true

  // Determine input type based on what's enabled
  let inputType = 'datetime-local';
  if (enableDate && !enableTime) {
    inputType = 'date';
  } else if (!enableDate && enableTime) {
    inputType = 'time';
  }

  return (
    <Input
      key={id}
      type={inputType}
      value={value}
      onChange={(e) => {
        if (valuePath) {
          onDataChange(valuePath, e.target.value);
        }
      }}
      className="max-w-xs"
    />
  );
}
