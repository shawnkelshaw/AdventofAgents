import { describe, it, expect } from 'vitest'
import { validateA2UIJson } from './A2UIRenderer'

describe('A2UI Renderer Utils', () => {
    describe('validateA2UIJson', () => {
        it('should return true for valid beginRendering', () => {
            const payload = [{
                beginRendering: {
                    surfaceId: 'test_surface',
                    root: 'root_id'
                }
            }]
            const result = validateA2UIJson(payload)
            expect(result.valid).toBe(true)
        })

        it('should return false for missing surfaceId', () => {
            const payload = [{
                beginRendering: {
                    root: 'root_id'
                }
            }]
            const result = validateA2UIJson(payload)
            expect(result.valid).toBe(false)
            expect(result.errors.some(e => e.message.includes('surfaceId'))).toBe(true)
        })

        it('should return false for unknown component type', () => {
            const payload = [{
                surfaceUpdate: {
                    surfaceId: 'test_surface',
                    components: [
                        {
                            id: 'root_id',
                            component: {
                                UnknownType: {}
                            } as any
                        }
                    ]
                }
            }]
            const result = validateA2UIJson(payload)
            expect(result.valid).toBe(false)
            expect(result.errors.some(e => e.message.includes('Unknown component type'))).toBe(true)
        })
    })
})
