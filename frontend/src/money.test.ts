import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatInr } from './money.ts'

test('crores', () => {
  assert.equal(formatInr(39800000), '₹3.98 crore')
  assert.equal(formatInr(10700000), '₹1.07 crore')
  assert.equal(formatInr(39800000, 'hi'), '₹3.98 करोड़')
})

test('below a crore uses lakh grouping', () => {
  assert.equal(formatInr(107000), '₹1,07,000')
  assert.equal(formatInr(9999999), '₹99,99,999')
})
