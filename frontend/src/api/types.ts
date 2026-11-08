/** Friendly aliases over the generated OpenAPI types. Never hand-write API shapes. */
import type { components } from "@/api/schema";

type Schemas = components["schemas"];

export type HealthResponse = Schemas["HealthResponse"];
export type ProfileOut = Schemas["ProfileOut"];
export type ProfilePatch = Schemas["ProfilePatch"];
export type ProfileResponse = Schemas["ProfileResponse"];
export type SkillLevel = Schemas["SkillLevel"];
export type SettingsOut = Schemas["SettingsOut"];
export type SettingsPatch = Schemas["SettingsPatch"];
export type TopicOut = Schemas["TopicOut"];
