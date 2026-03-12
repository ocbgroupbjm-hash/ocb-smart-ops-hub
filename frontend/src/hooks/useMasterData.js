import { useState, useEffect, useCallback } from 'react'

const API_URL = process.env.REACT_APP_BACKEND_URL

/**
 * Custom hooks untuk memuat master data dari API
 * Digunakan untuk searchable dropdowns
 */

// Generic fetch hook
function useMasterData(endpoint, token, mapFn, dependencies = []) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch')
      const json = await res.json()
      const items = json.items || json.data || json || []
      setData(Array.isArray(items) ? items.map(mapFn) : [])
      setError(null)
    } catch (err) {
      console.error(`Error fetching ${endpoint}:`, err)
      setError(err.message)
      setData([])
    } finally {
      setLoading(false)
    }
  }, [endpoint, token, ...dependencies])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

// Products
export function useProducts(token) {
  return useMasterData(
    '/api/products',
    token,
    (p) => ({
      value: p.id,
      label: p.name,
      sublabel: p.code || p.sku,
      code: p.code,
      sku: p.sku,
      price: p.sell_price || p.price,
      unit: p.unit,
      category: p.category,
    })
  )
}

// Customers
export function useCustomers(token) {
  return useMasterData(
    '/api/customers',
    token,
    (c) => ({
      value: c.id,
      label: c.name,
      sublabel: c.code || c.phone,
      code: c.code,
      phone: c.phone,
      address: c.address,
    })
  )
}

// Suppliers
export function useSuppliers(token) {
  return useMasterData(
    '/api/suppliers',
    token,
    (s) => ({
      value: s.id,
      label: s.name,
      sublabel: s.code || s.contact_person,
      code: s.code,
      phone: s.phone,
      address: s.address,
    })
  )
}

// Branches
export function useBranches(token) {
  return useMasterData(
    '/api/branches',
    token,
    (b) => ({
      value: b.id,
      label: b.name,
      sublabel: b.code,
      code: b.code,
      address: b.address,
    })
  )
}

// Warehouses
export function useWarehouses(token) {
  return useMasterData(
    '/api/warehouse',
    token,
    (w) => ({
      value: w.id,
      label: w.name,
      sublabel: w.code || w.branch_name,
      code: w.code,
      branch_id: w.branch_id,
      branch_name: w.branch_name,
    })
  )
}

// Users/Salespersons
export function useUsers(token, roleFilter = null) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    fetch(`${API_URL}/api/users`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(json => {
        let items = json.items || json.users || json || []
        if (roleFilter) {
          items = items.filter(u => u.role_code === roleFilter || u.role === roleFilter)
        }
        setData(items.map(u => ({
          value: u.id,
          label: u.name,
          sublabel: u.role_code || u.role || u.email,
          code: u.employee_code || u.code,
          email: u.email,
          role: u.role_code || u.role,
          branch_id: u.branch_id,
        })))
      })
      .catch(err => console.error('Error fetching users:', err))
      .finally(() => setLoading(false))
  }, [token, roleFilter])

  return { data, loading }
}

// Salespersons (filtered users)
export function useSalespersons(token) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    fetch(`${API_URL}/api/salespersons`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(json => {
        const items = json.items || json.salespersons || json || []
        setData(items.map(s => ({
          value: s.id,
          label: s.name,
          sublabel: s.code || s.employee_code,
          code: s.code || s.employee_code,
          branch_id: s.branch_id,
          branch_name: s.branch_name,
        })))
      })
      .catch(err => console.error('Error fetching salespersons:', err))
      .finally(() => setLoading(false))
  }, [token])

  return { data, loading }
}

// Categories
export function useCategories(token) {
  return useMasterData(
    '/api/products/categories',
    token,
    (c) => ({
      value: c.id || c.name || c,
      label: typeof c === 'string' ? c : (c.name || c.label),
    })
  )
}

// Brands
export function useBrands(token) {
  return useMasterData(
    '/api/products/brands',
    token,
    (b) => ({
      value: b.id || b.name || b,
      label: typeof b === 'string' ? b : (b.name || b.label),
    })
  )
}

// Chart of Accounts
export function useAccounts(token) {
  return useMasterData(
    '/api/accounts',
    token,
    (a) => ({
      value: a.id || a.code,
      label: `${a.code} - ${a.name}`,
      sublabel: a.type,
      code: a.code,
      name: a.name,
      type: a.type,
    })
  )
}

// Tax Types
export function useTaxTypes(token) {
  return useMasterData(
    '/api/tax-engine/tax-types',
    token,
    (t) => ({
      value: t.code,
      label: `${t.code} - ${t.name}`,
      sublabel: `${(t.rate * 100).toFixed(1)}%`,
      rate: t.rate,
    })
  )
}

export default {
  useProducts,
  useCustomers,
  useSuppliers,
  useBranches,
  useWarehouses,
  useUsers,
  useSalespersons,
  useCategories,
  useBrands,
  useAccounts,
  useTaxTypes,
}
