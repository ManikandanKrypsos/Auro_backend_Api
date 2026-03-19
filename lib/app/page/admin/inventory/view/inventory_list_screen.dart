import 'package:flutter/material.dart';
import 'package:get/route_manager.dart';

import '../../../../routes/names.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/add_button.dart';
import '../../../../widgets/app_search_bar.dart';
import '../../../../widgets/custom_appbar.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  int _selectedTab = 0;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  // ── Static Data ──────────────────────────────────────
  final List<Map<String, dynamic>> _allItems = const [
    {
      'name': '24K Gold Facial Serum',
      'category': 'CONSUMABLE',
      'subCategory': 'SKINCARE',
      'quantity': 12,
      'unit': 'pcs remaining',
      'status': 'LOW STOCK',
    },
    {
      'name': 'Organic Lavender Extract',
      'category': 'NATURAL',
      'subCategory': 'ESSENTIALS',
      'quantity': 84,
      'unit': 'units',
      'status': 'IN STOCK',
    },
    {
      'name': 'Hydra-Facial Pro Wand',
      'category': 'EQUIPMENT',
      'subCategory': 'FACIAL',
      'quantity': 4,
      'unit': 'units',
      'status': 'IN STOCK',
    },
    {
      'name': 'Surgical Grade Botox',
      'category': 'MEDICAL',
      'subCategory': 'INJECTABLES',
      'quantity': 0,
      'unit': 'units',
      'status': 'OUT OF STOCK',
    },
    {
      'name': 'Diamond Microdermabrasion Tips',
      'category': 'CONSUMABLE',
      'subCategory': 'EQUIPMENT',
      'quantity': 6,
      'unit': 'pcs remaining',
      'status': 'LOW STOCK',
    },
    {
      'name': 'Hyaluronic Acid Filler',
      'category': 'MEDICAL',
      'subCategory': 'INJECTABLES',
      'quantity': 22,
      'unit': 'units',
      'status': 'IN STOCK',
    },
    {
      'name': 'Rose Hip Oil Blend',
      'category': 'NATURAL',
      'subCategory': 'ESSENTIALS',
      'quantity': 0,
      'unit': 'units',
      'status': 'OUT OF STOCK',
    },
  ];

  // ── Tabs ─────────────────────────────────────────────
  static const _tabs = ['ALL ITEMS', 'LOW STOCK', 'OUT OF STOCK'];

  // ── Filtered List ────────────────────────────────────
  List<Map<String, dynamic>> get _filteredItems {
    List<Map<String, dynamic>> items;
    switch (_selectedTab) {
      case 1:
        items = _allItems.where((i) => i['status'] == 'LOW STOCK').toList();
        break;
      case 2:
        items = _allItems.where((i) => i['status'] == 'OUT OF STOCK').toList();
        break;
      default:
        items = _allItems;
    }
    if (_searchQuery.isNotEmpty) {
      items = items
          .where(
            (i) =>
                (i['name'] as String).toLowerCase().contains(
                  _searchQuery.toLowerCase(),
                ) ||
                (i['category'] as String).toLowerCase().contains(
                  _searchQuery.toLowerCase(),
                ),
          )
          .toList();
    }
    return items;
  }

  int get _lowWarningCount =>
      _allItems.where((i) => i['status'] == 'LOW STOCK').length;

  int get _outOfStockCount =>
      _allItems.where((i) => i['status'] == 'OUT OF STOCK').length;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'AURA INVENTORY'),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),

          // ── Search Bar ──
          AppSearchBar(
            hintText: 'Search inventory...',
            controller: _searchController,
            onChanged: (v) => setState(() => _searchQuery = v),
          ),
          const SizedBox(height: 20),

          // ── Tab Row ──
          _buildTabRow(),
          const SizedBox(height: 24),

          // ── Content ──
          Expanded(child: _buildList()),
        ],
      ),
      floatingActionButton: AddButton(
        onTap: () {
          Get.toNamed(PageRoutes.inventoryManageScreen);
        },
      ),
    );
  }

  // ── Tab Row ──────────────────────────────────────────
  Widget _buildTabRow() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: List.generate(_tabs.length, (i) {
          final isSelected = _selectedTab == i;
          return GestureDetector(
            onTap: () => setState(() => _selectedTab = i),
            child: Padding(
              padding: EdgeInsets.only(right: i < _tabs.length - 1 ? 32 : 0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _tabs[i],
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: isSelected
                          ? ColorResources.primaryColor
                          : ColorResources.liteTextColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    height: 1.5,
                    width: isSelected ? _tabs[i].length * 10.0 : 0,
                    color: ColorResources.primaryColor,
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }

  // ── List ─────────────────────────────────────────────
  Widget _buildList() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 100),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Stats Row ──
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  label: 'OUT OF STOCK',
                  value: '0$_outOfStockCount',
                  suffix: 'items',
                  valueColor: ColorResources.negativeColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  label: 'LOW WARNING',
                  value: '0$_lowWarningCount',
                  suffix: 'items',
                  valueColor: ColorResources.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // ── Items ──
          ..._filteredItems.map((item) => _buildInventoryCard(item)),

          if (_filteredItems.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 48),
                child: Text(
                  'NO ITEMS FOUND',
                  style: AppTextStyles.headingSmall.copyWith(
                    color: ColorResources.liteTextColor.withOpacity(0.4),
                    letterSpacing: 3,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  // ── Stat Card ────────────────────────────────────────
  Widget _buildStatCard({
    required String label,
    required String value,
    required String suffix,
    Color? valueColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor,
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: valueColor ?? ColorResources.whiteColor,
                  fontSize: 28,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 1,
                  height: 1,
                ),
              ),
              const SizedBox(width: 5),
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(
                  suffix,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 12,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ── Inventory Card ───────────────────────────────────
  Widget _buildInventoryCard(Map<String, dynamic> item) {
    final String status = item['status'] as String;
    final int quantity = item['quantity'] as int;

    Color statusColor;
    switch (status) {
      case 'LOW STOCK':
        statusColor = ColorResources.primaryColor;
        break;
      case 'OUT OF STOCK':
        statusColor = ColorResources.negativeColor;
        break;
      default:
        statusColor = ColorResources.positiveColor;
    }

    Color quantityColor;
    switch (status) {
      case 'LOW STOCK':
        quantityColor = ColorResources.primaryColor;
        break;
      case 'OUT OF STOCK':
        quantityColor = ColorResources.negativeColor;
        break;
      default:
        quantityColor = ColorResources.liteTextColor;
    }

    final String quantityText = quantity == 0
        ? '0 units'
        : '${quantity.toString().padLeft(2, '0')} ${item['unit']}';

    return GestureDetector(
      onTap: ()=>   Get.toNamed(PageRoutes.inventoryDetailScreen),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _buildStatusBadge(label: status, color: statusColor),
                const SizedBox(width: 8),
                Text(
                  '${item['category']} • ${item['subCategory']}',
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 10,
                    letterSpacing: 1.5,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    item['name'] as String,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 17,
                      fontWeight: FontWeight.w500,
                      letterSpacing: 0.3,
                    ),
                  ),
                ),
                Text(
                  'DETAILS',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.6),
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Expanded(
                  child: Text(
                    quantityText,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: quantityColor,
                      fontSize: 13,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ── Status Badge ─────────────────────────────────────
  Widget _buildStatusBadge({required String label, required Color color}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.3), width: 0.5),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: color,
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}
