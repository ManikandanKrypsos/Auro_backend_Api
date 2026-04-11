import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../theme/color/color.dart';
import '../../../../widgets/app_drop_down.dart';
import '../../../../widgets/custom_appbar.dart';

const List<String> _roomTypes = [
  'Therapy Suite',
  'Laser Room',
  'Relaxation Room',
  'Treatment Room',
  'Consultation Room',
];
 
class RoomManageScreen extends StatelessWidget {
  final Map<String, String>? room;
  const RoomManageScreen({super.key, this.room});
 
  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => _RoomManageCubit(room: room),
      child: _RoomManageBody(room: room),
    );
  }
}
 
// ── Manage Cubit ───────────────────────────────────────────
 
class _RoomManageState {
  final String selectedType;
  const _RoomManageState({required this.selectedType});
  _RoomManageState copyWith({String? selectedType}) =>
      _RoomManageState(
          selectedType: selectedType ?? this.selectedType);
}
 
class _RoomManageCubit extends Cubit<_RoomManageState> {
  _RoomManageCubit({Map<String, String>? room})
      : super(_RoomManageState(
          selectedType: room?['type'] ?? _roomTypes.first,
        ));
 
  void selectType(String type) =>
      emit(state.copyWith(selectedType: type));
}
 
// ── Manage Body ────────────────────────────────────────────
 
class _RoomManageBody extends StatelessWidget {
  final Map<String, String>? room;
 
  final _nameCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
 
  _RoomManageBody({this.room}) {
    if (room != null) {
      _nameCtrl.text = room!['name'] ?? '';
      _descCtrl.text = room!['description'] ?? '';
    }
  }
 
  bool get _isEditing => room != null;
 
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar:
          CustomAppBar(title: _isEditing ? 'EDIT ROOM' : 'ADD ROOM'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Section header ───────────────────────────
            _sectionHeader(Icons.meeting_room_outlined, 'ROOM DETAILS'),
 
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Room Name
                  _label('ROOM NAME'),
                  _inputField(
                    controller: _nameCtrl,
                    hint: 'Suite Lumière',
                  ),
 
                  const SizedBox(height: 20),
 
                  // Room Type
                  _label('ROOM TYPE'),
                  BlocBuilder<_RoomManageCubit, _RoomManageState>(
                    buildWhen: (p, c) =>
                        p.selectedType != c.selectedType,
                    builder: (context, state) {
                      return AppDropdown(
                        value: state.selectedType,
                        items: _roomTypes,
                        onChanged: (v) {
                          if (v != null)
                            context
                                .read<_RoomManageCubit>()
                                .selectType(v);
                        },
                      );
                    },
                  ),
 
                  const SizedBox(height: 20),
 
                  // Description
                  _label('DESCRIPTION'),
                  _inputField(
                    controller: _descCtrl,
                    hint:
                        'Describe the room setup and purpose...',
                    maxLines: 4,
                  ),
                ],
              ),
            ),
 
            const SizedBox(height: 36),
 
            // ── Save button ──────────────────────────────

            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: PrimaryButton(label:       _isEditing ? 'SAVE CHANGES' : 'ADD ROOM', onTap: (){}),
            )
           
 
           , const SizedBox(height: 12),
 
            // ── Cancel / Delete ──────────────────────────
            Center(
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  _isEditing ? 'DELETE ROOM' : 'CANCEL & DISCARD',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: _isEditing
                        ? ColorResources.negativeColor.withOpacity(0.7)
                        : ColorResources.whiteColor.withOpacity(0.35),
                    fontSize: 11,
                    letterSpacing: 2.0,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
 
  // ── Helpers ───────────────────────────────────────────────
  Widget _sectionHeader(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
      child: Row(
        children: [
          Icon(icon, color: ColorResources.primaryColor, size: 18),
          const SizedBox(width: 12),
          Text(
            text,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 15,
              fontWeight: FontWeight.w600,
              letterSpacing: 3.5,
            ),
          ),
        ],
      ),
    );
  }
 
  Widget _label(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.liteTextColor,
          fontSize: 10,
          fontWeight: FontWeight.w600,
          letterSpacing: 2.5,
        ),
      ),
    );
  }
 
  Widget _inputField({
    required TextEditingController controller,
    String? hint,
    int maxLines = 1,
  }) {
    return TextField(
      controller: controller,
      maxLines: maxLines,
      style: const TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.whiteColor,
        fontSize: 15,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor.withOpacity(0.25),
          fontSize: 15,
          fontStyle: FontStyle.italic,
        ),
        filled: true,
        fillColor: ColorResources.cardColor,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
              color: ColorResources.borderColor, width: 0.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
              color: ColorResources.borderColor, width: 0.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
              color: ColorResources.primaryColor, width: 0.8),
        ),
      ),
      cursorColor: ColorResources.primaryColor,
    );
  }
}
 
