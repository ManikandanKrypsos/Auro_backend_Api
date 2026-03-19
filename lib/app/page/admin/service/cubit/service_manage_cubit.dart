import 'package:bloc/bloc.dart';


part 'service_manage_state.dart';

class ServiceManageCubit extends Cubit<ServiceManageState> {
  ServiceManageCubit({Map<String, dynamic>? service})
      : super(ServiceManageState(
          categoryTab: (service?['category'] as String?) == 'body' ? 1 : 0,
        ));
 
  // ── Category ───────────────────────────────────────────
  void selectCategory(int index) =>
      emit(state.copyWith(categoryTab: index));
 
  // ── Contraindications ──────────────────────────────────
  void addContraindication(String value) {
    if (value.trim().isEmpty) return;
    if (state.contraindications.contains(value)) return;
    emit(state.copyWith(
        contraindications: [...state.contraindications, value]));
  }
 
  void removeContraindication(String value) {
    emit(state.copyWith(
        contraindications:
            state.contraindications.where((e) => e != value).toList()));
  }
 
  // ── Frequency unit ─────────────────────────────────────
  void selectFreqUnit(String unit) =>
      emit(state.copyWith(freqUnit: unit));
 
  // ── Room ───────────────────────────────────────────────
  void selectRoom(String room) =>
      emit(state.copyWith(roomType: room));
 
  // ── Equipment ──────────────────────────────────────────
  void addEquipment(String value) {
    if (state.equipmentTags.contains(value)) return;
    emit(state.copyWith(equipmentTags: [...state.equipmentTags, value]));
  }
 
  void removeEquipment(String value) {
    emit(state.copyWith(
        equipmentTags:
            state.equipmentTags.where((e) => e != value).toList()));
  }
 
  // ── Consumables ────────────────────────────────────────
  void addConsumable(String value) {
    if (state.consumableTags.contains(value)) return;
    emit(state.copyWith(
        consumableTags: [...state.consumableTags, value]));
  }
 
  void removeConsumable(String value) {
    emit(state.copyWith(
        consumableTags:
            state.consumableTags.where((e) => e != value).toList()));
  }
 
  // ── Staff ──────────────────────────────────────────────
  void addStaff(String name) {
    if (state.assignedStaff.contains(name)) return;
    emit(state.copyWith(assignedStaff: [...state.assignedStaff, name]));
  }
 
  void removeStaff(String name) {
    emit(state.copyWith(
        assignedStaff:
            state.assignedStaff.where((e) => e != name).toList()));
  }
}
 
