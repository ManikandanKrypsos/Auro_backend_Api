import 'package:aura/app/routes/names.dart';
import 'package:aura/app/widgets/app_search_bar.dart';
import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../../theme/color/color.dart';
import '../../../../widgets/add_button.dart';

class _RoomState {
  final List<Map<String, String>> all;
  final List<Map<String, String>> filtered;
  final String query;

  const _RoomState({
    required this.all,
    required this.filtered,
    required this.query,
  });

  _RoomState copyWith({
    List<Map<String, String>>? all,
    List<Map<String, String>>? filtered,
    String? query,
  }) =>
      _RoomState(
        all: all ?? this.all,
        filtered: filtered ?? this.filtered,
        query: query ?? this.query,
      );
}

class _RoomCubit extends Cubit<_RoomState> {
  _RoomCubit()
      : super(_RoomState(
          all: _initial,
          filtered: _initial,
          query: '',
        ));

  static const List<Map<String, String>> _initial = [
    {
      'name': 'Suite Lumière',
      'type': 'Therapy Suite',
      'description':
          'Premium facial suite with ambient lighting and gold-finish fixtures.',
    },
    {
      'name': 'Laser Room One',
      'type': 'Laser Room',
      'description':
          'Advanced laser treatment room with clinical-grade ventilation.',
    },
    {
      'name': 'Relaxation Lounge',
      'type': 'Relaxation Room',
      'description':
          'Tranquil post-treatment recovery space with heated loungers.',
    },
    {
      'name': 'Suite Serenity',
      'type': 'Therapy Suite',
      'description':
          'Full-body treatment suite with integrated sound therapy system.',
    },
    {
      'name': 'Dermapen Studio',
      'type': 'Treatment Room',
      'description':
          'Specialist microneedling and dermal treatment chamber.',
    },
  ];

  void search(String q) {
    final filtered = q.isEmpty
        ? state.all
        : state.all
            .where((r) =>
                r['name']!.toLowerCase().contains(q.toLowerCase()) ||
                r['type']!.toLowerCase().contains(q.toLowerCase()))
            .toList();
    emit(state.copyWith(query: q, filtered: filtered));
  }
}

// ═══════════════════════════════════════════════════════════
// ROOM LIST SCREEN
// ═══════════════════════════════════════════════════════════

class RoomListScreen extends StatelessWidget {
  const RoomListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => _RoomCubit(),
      child: const _RoomListBody(),
    );
  }
}

class _RoomListBody extends StatelessWidget {
  const _RoomListBody();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'ROOMS'),
      floatingActionButton: AddButton(
        onTap: () => Get.toNamed(PageRoutes.roomManageScreen),
      ),
      body: Column(
        children: [
          const SizedBox(height: 16),
          AppSearchBar(
            hintText: 'Search rooms...',
            onChanged: (v) => context.read<_RoomCubit>().search(v),
          ),
          const SizedBox(height: 20),
          const Expanded(child: _RoomList()),
        ],
      ),
    );
  }
}

class _RoomList extends StatelessWidget {
  const _RoomList();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<_RoomCubit, _RoomState>(
      builder: (context, state) {
        if (state.filtered.isEmpty) {
          return Center(
            child: Text(
              'NO ROOMS FOUND',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor.withOpacity(0.4),
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 3.0,
              ),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 120),
          itemCount: state.filtered.length,
          itemBuilder: (context, i) => _RoomCard(room: state.filtered[i]),
        );
      },
    );
  }
}

class _RoomCard extends StatelessWidget {
  final Map<String, String> room;
  const _RoomCard({required this.room});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.roomManageScreen),
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
            // ── Type Badge + Room Type label ──
            Row(
              children: [
                _buildTypeBadge(room['type']!),
              ],
            ),
            const SizedBox(height: 10),

            // ── Name + Chevron ──
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    room['name']!,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 17,
                      fontWeight: FontWeight.w500,
                      letterSpacing: 0.3,
                    ),
                  ),
                ),
                Icon(
                  Icons.chevron_right,
                  color: ColorResources.liteTextColor.withOpacity(0.5),
                  size: 18,
                ),
              ],
            ),
            const SizedBox(height: 4),

            // ── Description ──
            Text(
              room['description']!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor.withOpacity(0.6),
                fontSize: 12,
                letterSpacing: 0.2,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTypeBadge(String type) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: ColorResources.primaryColor.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
        border:
            Border.all(color: ColorResources.primaryColor.withOpacity(0.3), width: 0.5),
      ),
      child: Text(
        type.toUpperCase(),
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.primaryColor,
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}